"""Role persistence through Papilio's native PostgreSQL repository."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import select
from sqlmodel import col

from src.apps.core.roles.domain.models.records import RoleModel
from src.apps.core.roles.infra.pg.tables import RoleTable


class RoleRepository(PGPersistenceRepository[RoleModel]):
    table = RoleTable

    async def find_by_key(self, key: str) -> RoleModel | None:
        """Read a role by its exact, case-sensitive key.

        Args:
            key: Stored role key, passed unchanged as a bound value.

        Returns:
            The role, including inactive records; None when absent.
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
    ) -> PagedType[RoleModel]:
        """Read an ID-ordered role page without loading scope assignments.

        Args:
            limit: Positive maximum number of roles to retrieve.
            offset: Nonnegative number of matching roles to skip.
            title: Literal case-insensitive substring; None skips filtering.
            is_active: Stored role flag; None includes both states.

        Returns:
            Matching roles and their total before pagination.

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
