"""Scope persistence using Papilio's native PostgreSQL repository."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import select
from sqlmodel import col

from src.apps.core.scopes.domain.models.records import ScopeModel
from src.apps.core.scopes.infra.pg.tables import ScopeTable


class ScopeRepository(PGPersistenceRepository[ScopeModel]):
    table = ScopeTable

    async def find_by_key(self, key: str) -> ScopeModel | None:
        """Read one scope by its exact, case-sensitive key.

        Args:
            key: User-defined key, passed as a bound SQL value unchanged.

        Returns:
            The stored scope, including inactive scopes; None when absent.
        """
        stmt = select(self.table).where(col(self.table.key) == key)
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        title: str | None = None,
        is_active: bool | None = None,
    ) -> PagedType[ScopeModel]:
        """Read an ID-ordered page and its related total count.

        Args:
            limit: Positive maximum number of rows to retrieve.
            offset: Nonnegative number of matching rows to skip.
            title: Literal case-insensitive title substring; None skips search.
            is_active: Filter by stored flag; None includes both states.

        Returns:
            Materialized matching rows and the total before pagination.

        Raises:
            ValueError: Limit is nonpositive or offset is negative.
        """
        stmt = select(self.table).order_by(col(self.table.id))
        if title is not None:
            stmt = stmt.where(
                col(self.table.title).icontains(title, autoescape=True)
            )
        if is_active is not None:
            stmt = stmt.where(col(self.table.is_active) == is_active)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page
