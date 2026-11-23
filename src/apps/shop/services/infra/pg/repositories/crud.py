"""PostgreSQL CRUD and filtered pages for shop services."""

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy.exc import IntegrityError
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
        where = []
        if q is not None:
            where.append(col(table.title).icontains(q, autoescape=True))
        if is_active is not None:
            where.append(col(table.is_active).is_(is_active))
        page = await self.get_page(
            where=where,
            order_by=[col(table.priority).asc(), col(table.id).asc()],
            limit=limit,
            offset=offset,
        )
        return page

    async def remove_by_id(self, id: int) -> ServiceModel | None:
        """Remove one service or report a PostgreSQL reference conflict."""
        try:
            service = await super().remove_by_id(id)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) != "23503":
                raise
            raise ConflictException(
                message="This service is still referenced.",
                message_code="service_in_use",
                unique_dict={},
            ) from error
        return service
