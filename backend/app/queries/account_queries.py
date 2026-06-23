from __future__ import annotations
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import AccountNotFoundError


async def get_balance(account_id: UUID, session: AsyncSession) -> dict:
    result = await session.execute(
        text("""
            SELECT account_id, owner_name, balance, currency, status,
                   version, last_updated
            FROM   account_balance_view
            WHERE  account_id = CAST(:account_id AS uuid)
        """),
        {"account_id": str(account_id)},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise AccountNotFoundError(str(account_id))
    return dict(row)


async def get_transactions(
    account_id: UUID,
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    result = await session.execute(
        text("""
            SELECT id, account_id, event_type, amount,
                   balance_after, description, occurred_at
            FROM   transaction_history_view
            WHERE  account_id = CAST(:account_id AS uuid)
            ORDER BY occurred_at DESC
            LIMIT  :limit OFFSET :offset
        """),
        {"account_id": str(account_id), "limit": limit, "offset": offset},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_all_accounts(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        text("""
            SELECT account_id, owner_name, balance, currency, status, last_updated
            FROM   account_balance_view
            ORDER BY last_updated DESC
        """)
    )
    return [dict(row) for row in result.mappings().all()]


async def get_event_stream(
    account_id: UUID,
    session: AsyncSession,
) -> list[dict]:
    """Raw event log — used by the EventStream debug view in the frontend."""
    result = await session.execute(
        text("""
            SELECT id, stream_id, version, event_type, payload,
                   correlation_id, occurred_at
            FROM   events
            WHERE  stream_id = CAST(:stream_id AS uuid)
            ORDER BY version ASC
        """),
        {"stream_id": str(account_id)},
    )
    return [dict(row) for row in result.mappings().all()]