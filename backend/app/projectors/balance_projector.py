from __future__ import annotations
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import (
    AccountClosed,
    AccountOpened,
    DomainEvent,
    MoneyDeposited,
    MoneyWithdrawn,
)

logger = logging.getLogger(__name__)


class BalanceProjector:
    """
    Maintains account_balance_view.
    Registered with the event bus at startup; called after every command.
    """

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    async def __call__(self, event: DomainEvent) -> None:
        async with self._session_factory() as session:
            match event:
                case AccountOpened():
                    await self._on_opened(session, event)
                case MoneyDeposited():
                    await self._on_deposited(session, event)
                case MoneyWithdrawn():
                    await self._on_withdrawn(session, event)
                case AccountClosed():
                    await self._on_closed(session, event)
            await session.commit()

    async def _on_opened(self, session: AsyncSession, event: AccountOpened) -> None:
        await session.execute(
            text("""
                INSERT INTO account_balance_view
                    (account_id, owner_name, balance, currency, status, version)
                VALUES
                    (:account_id, :owner_name, :balance, :currency, 'active', 1)
                ON CONFLICT (account_id) DO UPDATE SET
                    owner_name   = EXCLUDED.owner_name,
                    balance      = EXCLUDED.balance,
                    currency     = EXCLUDED.currency,
                    status       = 'active',
                    version      = account_balance_view.version + 1,
                    last_updated = now()
            """),
            {
                "account_id": str(event.account_id),
                "owner_name": event.owner_name,
                "balance":    event.initial_balance,
                "currency":   event.currency,
            },
        )

    async def _on_deposited(self, session: AsyncSession, event: MoneyDeposited) -> None:
        await session.execute(
            text("""
                UPDATE account_balance_view
                SET    balance      = balance + :amount,
                       version      = version + 1,
                       last_updated = now()
                WHERE  account_id = CAST(:account_id AS uuid)
            """),
            {"amount": event.amount, "account_id": str(event.account_id)},
        )

    async def _on_withdrawn(self, session: AsyncSession, event: MoneyWithdrawn) -> None:
        await session.execute(
            text("""
                UPDATE account_balance_view
                SET    balance      = balance - :amount,
                       version      = version + 1,
                       last_updated = now()
                WHERE  account_id = CAST(:account_id AS uuid)
            """),
            {"amount": event.amount, "account_id": str(event.account_id)},
        )

    async def _on_closed(self, session: AsyncSession, event: AccountClosed) -> None:
        await session.execute(
            text("""
                UPDATE account_balance_view
                SET    status       = 'closed',
                       version      = version + 1,
                       last_updated = now()
                WHERE  account_id = CAST(:account_id AS uuid)
            """),
            {"account_id": str(event.account_id)},
        )