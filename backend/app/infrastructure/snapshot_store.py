from __future__ import annotations
import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.aggregate import AccountAggregate


class SnapshotStore:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, aggregate: AccountAggregate) -> None:
        await self._session.execute(
            text("""
                INSERT INTO snapshots (stream_id, version, aggregate_type, state)
                VALUES (
                    CAST(:stream_id AS uuid),
                    :version,
                    :agg_type,
                    CAST(:state AS jsonb)
                )
                ON CONFLICT (stream_id, version) DO NOTHING
            """),
            {
                "stream_id": str(aggregate.account_id),
                "version":   aggregate.version,
                "agg_type":  "AccountAggregate",
                "state":     json.dumps(aggregate.to_snapshot()),
            },
        )
        await self._session.commit()

    async def load_latest(self, stream_id: UUID) -> AccountAggregate | None:
        result = await self._session.execute(
            text("""
                SELECT state FROM snapshots
                WHERE  stream_id = CAST(:stream_id AS uuid)
                ORDER BY version DESC
                LIMIT 1
            """),
            {"stream_id": str(stream_id)},
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return AccountAggregate.from_snapshot(dict(row))