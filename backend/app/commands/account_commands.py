from __future__ import annotations
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.aggregate import AccountAggregate
from app.domain.commands import (
    CloseAccountCommand,
    DepositMoneyCommand,
    OpenAccountCommand,
    WithdrawMoneyCommand,
)
from app.domain.exceptions import AccountNotFoundError
from app.infrastructure.event_bus import InProcessEventBus
from app.infrastructure.event_store import EventStore
from app.infrastructure.snapshot_store import SnapshotStore


async def _load(
    account_id: UUID,
    session: AsyncSession,
) -> AccountAggregate:
    """
    Load an aggregate, preferring snapshots then replaying the delta.
    Raises AccountNotFoundError if no events exist for the stream.
    """
    snapshot_store = SnapshotStore(session)
    event_store    = EventStore(session)

    agg = await snapshot_store.load_latest(account_id)
    after_version = agg.version if agg else 0
    if agg is None:
        agg = AccountAggregate(account_id=account_id)

    events = await event_store.load_stream(account_id, after_version=after_version)
    if not events and after_version == 0:
        raise AccountNotFoundError(str(account_id))

    for event in events:
        agg._apply_saved(event)

    return agg


async def _save_and_publish(
    agg: AccountAggregate,
    session: AsyncSession,
    bus: InProcessEventBus,
) -> None:
    event_store    = EventStore(session)
    snapshot_store = SnapshotStore(session)

    # agg.version is now the version AFTER all pending events were applied.
    # expected_version = the version BEFORE = current - number of pending events.
    expected_version = agg.version - len(agg._pending_events)
    await event_store.append_events(
        stream_id=agg.account_id,
        events=agg._pending_events,
        expected_version=expected_version,
    )

    if agg.should_snapshot:
        await snapshot_store.save(agg)

    await bus.publish(agg._pending_events)
    agg._pending_events.clear()


# ── Handlers ──────────────────────────────────────────────────────────────────

async def handle_open_account(
    cmd: OpenAccountCommand,
    session: AsyncSession,
    bus: InProcessEventBus,
) -> UUID:
    agg = AccountAggregate()
    agg.open(
        owner_name=cmd.owner_name,
        initial_balance=cmd.initial_balance,
        currency=cmd.currency,
    )
    # Newly opened account: expected_version = 0
    event_store = EventStore(session)
    await event_store.append_events(
        stream_id=agg.account_id,
        events=agg._pending_events,
        expected_version=0,
    )
    await bus.publish(agg._pending_events)
    agg._pending_events.clear()
    return agg.account_id


async def handle_deposit(
    cmd: DepositMoneyCommand,
    session: AsyncSession,
    bus: InProcessEventBus,
) -> None:
    agg = await _load(cmd.account_id, session)
    agg.deposit(amount=cmd.amount, description=cmd.description)
    await _save_and_publish(agg, session, bus)


async def handle_withdraw(
    cmd: WithdrawMoneyCommand,
    session: AsyncSession,
    bus: InProcessEventBus,
) -> None:
    agg = await _load(cmd.account_id, session)
    agg.withdraw(amount=cmd.amount, description=cmd.description)
    await _save_and_publish(agg, session, bus)


async def handle_close_account(
    cmd: CloseAccountCommand,
    session: AsyncSession,
    bus: InProcessEventBus,
) -> None:
    agg = await _load(cmd.account_id, session)
    agg.close(reason=cmd.reason)
    await _save_and_publish(agg, session, bus)