from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.dependencies import BusDep, SessionDep
from app.infrastructure.event_store import EventStore
from app.domain.events import EVENT_REGISTRY
from decimal import Decimal
from uuid import UUID

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/rebuild-projection")
async def rebuild_projection(session: SessionDep, bus: BusDep):
    """
    Truncate both read-model tables then replay every event in the store
    in chronological order.

    Why this matters (mention in interviews):
    - Add a new projection in the future → just replay
    - Fix a buggy projector → truncate + replay
    - Zero data loss: the event store is the source of truth
    """
    # 1. Wipe read models
    await session.execute(text("TRUNCATE TABLE account_balance_view"))
    await session.execute(text("TRUNCATE TABLE transaction_history_view"))
    await session.commit()

    # 2. Stream all events in order and re-publish through the bus
    event_store = EventStore(session)
    offset = 0
    replayed = 0

    while True:
        raw_rows = await event_store.load_all_events(after_position=offset, batch_size=500)
        if not raw_rows:
            break

        for row in raw_rows:
            event_class = EVENT_REGISTRY.get(row["event_type"])
            if event_class is None:
                continue

            payload = dict(row["payload"])
            for key in ("amount", "initial_balance"):
                if key in payload:
                    payload[key] = Decimal(payload[key])
            for key in ("account_id",):
                if key in payload:
                    payload[key] = UUID(payload[key])

            event = event_class(**payload)
            await bus.publish([event])
            replayed += 1

        offset += len(raw_rows)
        if len(raw_rows) < 500:
            break

    return {"replayed": replayed, "status": "ok"}


@router.get("/stats")
async def stats(session: SessionDep):
    """Quick health/stats snapshot — useful in the Grafana dashboard."""
    result = await session.execute(text("""
        SELECT
            (SELECT COUNT(*)              FROM events)                  AS total_events,
            (SELECT COUNT(DISTINCT stream_id) FROM events)             AS total_streams,
            (SELECT COUNT(*)              FROM account_balance_view)   AS total_accounts,
            (SELECT COUNT(*)              FROM transaction_history_view) AS total_transactions,
            (SELECT COUNT(*)              FROM snapshots)              AS total_snapshots
    """))
    row = result.mappings().one()
    return dict(row)