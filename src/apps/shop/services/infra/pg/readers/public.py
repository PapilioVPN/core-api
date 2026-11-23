"""PostgreSQL selections for active service cards."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.schemas.results import PagedType
from sqlalchemy import func, select
from sqlmodel import col

from src.apps.shop.services.domain.results.public import PublicService
from src.apps.shop.services.infra.pg.tables import ServiceTable


class PublicServiceReader(PGReader):
    async def search(
        self, *, q: str | None, limit: int, offset: int
    ) -> PagedType[PublicService]:
        """Search active services by literal title substring.

        Args:
            q: Optional case-insensitive substring.
            limit: Maximum number of services to return.
            offset: Number of matching services to skip.

        Returns:
            A priority/ID-ordered page with its total before pagination.
        """
        table = ServiceTable
        query = select(
            col(table.id), col(table.title), col(table.description)
        ).where(col(table.is_active).is_(True))
        if q is not None:
            query = query.where(col(table.title).icontains(q, autoescape=True))
        stmt = select(func.count()).select_from(query.subquery())
        count = await self.uow.execute(stmt)
        total = count.scalar_one()
        items: list[PublicService] = []
        if offset < total:
            stmt = (
                query.order_by(col(table.priority), col(table.id))
                .limit(limit)
                .offset(offset)
            )
            result = await self.uow.execute(stmt)
            items = [PublicService(*row) for row in result.tuples()]
        return PagedType(items=items, total_items=total)
