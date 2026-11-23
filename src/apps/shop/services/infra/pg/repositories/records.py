"""PostgreSQL writes and paged selections for shop services."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import select
from sqlmodel import col

from src.apps.shop.services.domain.models.records import ServiceModel
from src.apps.shop.services.infra.pg.tables import ServiceTable


class ServiceRepository(PGPersistenceRepository[ServiceModel]):
    table = ServiceTable

    async def list(
        self, *, limit: int, offset: int, q: str | None, is_active: bool | None
    ) -> PagedType[ServiceModel]:
        """Read matching services in priority and ID order.

        Args:
            limit: Maximum number of rows to retrieve.
            offset: Matching rows to skip.
            q: Literal title substring, when supplied.
            is_active: Optional filter for the sales state.

        Returns:
            Matching rows and their total before pagination.
        """
        table = self.table
        stmt = select(table).order_by(col(table.priority), col(table.id))
        if q is not None:
            stmt = stmt.where(col(table.title).icontains(q, autoescape=True))
        if is_active is not None:
            stmt = stmt.where(col(table.is_active) == is_active)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page
