"""Atomic refresh-consumption insertion without transaction ownership."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.core.access.tokens.domain.models.refresh import RefreshUseModel
from src.apps.core.access.tokens.infra.pg.tables import RefreshUseTable


class RefreshUseRepository(PGPersistenceRepository[RefreshUseModel]):
    table = RefreshUseTable

    async def insert_if_absent(self, data: RefreshUseModel) -> bool:
        """Insert one identity without changing an existing consumption record.

        Args:
            data: Trusted audience, token identity and original expiration.

        Returns:
            True when this transaction inserted the identity; False on a unique
            conflict. The caller owns commit and rollback. No SELECT or retry.
        """
        stmt = (
            insert(self.table)
            .values(data.to_row())
            .on_conflict_do_nothing(constraint="uq_refresh_use")
            .returning(col(self.table.id))
        )
        result = await self.uow.execute(stmt)
        inserted = result.scalar_one_or_none() is not None
        return inserted

    async def remove_expired(self, *, before: datetime, limit: int) -> int:
        """Remove a bounded set of records whose supplied expiry has passed.

        Args:
            before: Explicit aware cutoff; expiration policy stays in app.
            limit: Trusted maximum records removed in this one statement.

        Returns:
            Actual number removed; unexpired records are preserved. This raw
            maintenance operation neither validates tokens nor commits SQL.
        """
        ids = (
            select(col(self.table.id))
            .where(col(self.table.expires_at) <= before)
            .order_by(col(self.table.expires_at), col(self.table.id))
            .limit(limit)
        )
        stmt = (
            delete(self.table)
            .where(col(self.table.id).in_(ids))
            .returning(col(self.table.id))
        )
        result = await self.uow.execute(stmt)
        removed = len(result.scalars().all())
        return removed
