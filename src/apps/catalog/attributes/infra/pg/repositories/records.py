"""Native attribute persistence and paged reads."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import or_, select
from sqlmodel import col

from src.apps.catalog.attributes.domain.models.records import AttributeModel
from src.apps.catalog.attributes.infra.pg.tables import AttributeTable


class AttributeRepository(PGPersistenceRepository[AttributeModel]):
    table = AttributeTable

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None,
        is_active: bool | None,
    ) -> PagedType[AttributeModel]:
        """Read matching attributes ordered by label and identity.

        Args:
            limit: Maximum rows.
            offset: Matching rows to skip.
            q: Literal label or key substring, when supplied.
            is_active: Optional state selection.

        Returns:
            Matching rows and their total before pagination.
        """
        table = self.table
        stmt = select(table).order_by(col(table.label), col(table.id))
        if q is not None:
            stmt = stmt.where(
                or_(
                    col(table.label).icontains(q, autoescape=True),
                    col(table.key).icontains(q, autoescape=True),
                )
            )
        if is_active is not None:
            stmt = stmt.where(col(table.is_active) == is_active)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page
