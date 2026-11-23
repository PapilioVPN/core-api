"""Native persistence and bounded category reads."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import or_, select
from sqlmodel import col

from src.apps.catalog.categories.domain.models.records import CategoryModel
from src.apps.catalog.categories.infra.pg.tables import CategoryTable


class CategoryRepository(PGPersistenceRepository[CategoryModel]):
    table = CategoryTable

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        is_active: bool | None,
    ) -> PagedType[CategoryModel]:
        """Read a priority-ordered page of matching categories.

        Args:
            limit: Maximum rows.
            offset: Matching rows to skip.
            q: Literal title or slug substring, when supplied.
            is_active: Optional state selection.

        Returns:
            Matching rows and their total before pagination.
        """
        table = self.table
        stmt = select(table).order_by(col(table.priority), col(table.id))
        if q is not None:
            stmt = stmt.where(
                or_(
                    col(table.title).icontains(q, autoescape=True),
                    col(table.slug).icontains(q, autoescape=True),
                )
            )
        if is_active is not None:
            stmt = stmt.where(col(table.is_active) == is_active)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page
