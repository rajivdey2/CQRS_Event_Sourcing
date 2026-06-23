from __future__ import annotations
import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import DomainEvent, EVENT_REGISTRY
from app.domain.exceptions import ConcurrencyConflictError


class EventStore:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append_events(
        self,
        stream_id: UUID,
        events: list[DomainEvent],
        expected_version: int,
    ) -> None:
        if not events:
            return

        rows = []
        for i, event in enumerate(events):
            rows.append({
                "stream_id":      str(stream_id),
                "version":        expected_version + i + 1,
                "event_type":     event.event_type,
                "payload":        json.dumps(event.to_dict()),
                "correlation_id": str(event.correlation_id) if event.correlation_id else None,
                "causation_id":   str(event.causation_id)   if event.causation_id   else None,
                "occurred_at":    event.occurred_at,
            })

        try:
            # ✅ Use CAST(:param AS type) — never :: with SQLAlchemy text()
            # The :: shorthand conflicts with SQLAlchemy's asyncpg param
            # substitution which replaces :name with $N positional markers.
            await self._session.execute(
                text("""
                    INSERT INTO events
                        (stream_id, version, event_type, payload,
                         correlation_id, causation_id, occurred_at)
                    VALUES (
                        CAST(:stream_id      AS uuid),
                        :version,
                        :event_type,
                        CAST(:payload        AS jsonb),
                        CAST(:correlation_id AS uuid),
                        CAST(:causation_id   AS uuid),
                        :occurred_at
                    )
                """),
                rows,
            )
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise ConcurrencyConflictError(str(stream_id), expected_version + 1)

    async def load_stream(
        self,
        stream_id: UUID,
        after_version: int = 0,
    ) -> list[DomainEvent]:
        result = await self._session.execute(
            text("""
                SELECT id            AS event_id,
                       event_type,
                       payload,
                       occurred_at,
                       correlation_id,
                       causation_id
                FROM   events
                WHERE  stream_id = CAST(:stream_id AS uuid)
                  AND  version   > :after_version
                ORDER BY version ASC
            """),
            {"stream_id": str(stream_id), "after_version": after_version},
        )
        return [self._deserialise(row) for row in result.mappings().all()]

    async def load_all_events(
        self,
        after_position: int = 0,
        batch_size: int = 500,
    ) -> list[dict]:
        result = await self._session.execute(
            text("""
                SELECT id, stream_id, version, event_type, payload, occurred_at
                FROM   events
                ORDER BY occurred_at ASC, version ASC
                LIMIT  :batch_size OFFSET :offset
            """),
            {"batch_size": batch_size, "offset": after_position},
        )
        return [dict(row) for row in result.mappings().all()]

    def _deserialise(self, row: dict) -> DomainEvent:
        event_class = EVENT_REGISTRY.get(row["event_type"])
        if event_class is None:
            raise ValueError(f"Unknown event type: {row['event_type']}")

        payload = dict(row["payload"])

        for key in ("amount", "initial_balance"):
            if key in payload:
                payload[key] = Decimal(payload[key])

        for key in ("account_id",):
            if key in payload:
                payload[key] = UUID(payload[key])

        # Merge stored metadata back — restores original event_id, timestamps,
        # and correlation IDs instead of generating new defaults on replay.
        payload["event_id"]       = UUID(str(row["event_id"]))
        payload["occurred_at"]    = row["occurred_at"]
        payload["correlation_id"] = UUID(str(row["correlation_id"])) if row["correlation_id"] else None
        payload["causation_id"]   = UUID(str(row["causation_id"]))   if row["causation_id"]   else None

        return event_class(**payload)