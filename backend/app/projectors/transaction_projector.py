from __future__ import annotations
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import (
    AccountOpened,
    DomainEvent,
    MoneyDeposited,
    MoneyWithdrawn,
)

logger = logging.getLogger(__name__)


class TransactionProjector:
    """
    Maintains transaction_history_view.
    Uses event_id as idempotency key — safe to replay events multiple times.
    """

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    async def __call__(self, event: DomainEvent) -> None:
        async with self._session_factory() as session:
            match event:
                case AccountOpened() if event.initial_balance > 0:
                    await self._insert(
                        session,
                        event=event,
                        event_type="AccountOpened",
                        amount=event.initial_balance,
                        description="Initial deposit",
                    )
                case MoneyDeposited():
                    await self._insert(
                        session,
                        event=event,
                        event_type="MoneyDeposited",
                        amount=event.amount,
                        description=event.description,
                    )
                case MoneyWithdrawn():
                    await self._insert(
                        session,
                        event=event,
                        event_type="MoneyWithdrawn",
                        amount=event.amount,
                        description=event.description,
                    )
                case _:
                    return  # AccountClosed has no transaction row
            await session.commit()

    async def _insert(
        self,
        session: AsyncSession,
        event: DomainEvent,
        event_type: str,
        amount,
        description: str,
    ) -> None:
        await session.execute(
            text("""
                INSERT INTO transaction_history_view
                    (account_id, event_id, event_type, amount, description, occurred_at)
                VALUES
                    (:account_id, :event_id, :event_type, :amount, :description, :occurred_at)
                ON CONFLICT (event_id) DO NOTHING
            """),
            {
                "account_id":  str(event.account_id),
                "event_id":    str(event.event_id),
                "event_type":  event_type,
                "amount":      amount,
                "description": description,
                "occurred_at": event.occurred_at,
            },
        )