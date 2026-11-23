"""Search published catalogs under one active service."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.schemas.results import PagedType
from sqlalchemy import func, select
from sqlmodel import col

from src.apps.shop.products.catalogs.domain.dtos.public import (
    ServiceCatalogSearch,
)
from src.apps.shop.products.catalogs.domain.results.public import PublicCatalog
from src.apps.shop.products.catalogs.infra.pg.sql.public import (
    visible_catalogs,
)
from src.apps.shop.products.catalogs.infra.pg.tables import CatalogTable
from src.apps.shop.products.services.infra.pg.tables import ServiceTable


class ServiceCatalogReader(PGReader):
    async def search(
        self,
        service_id: int,
        data: ServiceCatalogSearch,
        *,
        limit: int,
        offset: int,
    ) -> PagedType[PublicCatalog] | None:
        """Read one active service's catalog matches and their total.

        Args:
            service_id: Required parent service identity.
            data: Validated title, volume and expiry filters.
            limit: Maximum number of offers to return.
            offset: Number of matching offers to skip.

        Returns:
            A priority/ID-ordered page with an empty page for no matches.
            None means the parent is absent or inactive.
        """
        table = CatalogTable
        query = visible_catalogs().where(col(table.service_id) == service_id)
        if data.q is not None:
            query = query.where(
                col(table.title).icontains(data.q, autoescape=True)
            )
        if data.is_unlimited is not None:
            query = query.where(
                col(table.volume_id).is_(None) == data.is_unlimited
            )
        if data.has_expiry is not None:
            query = query.where(
                col(table.duration_id).is_not(None) == data.has_expiry
            )

        matches = query.with_only_columns(
            col(table.id), col(table.service_id)
        ).subquery()
        stmt = (
            select(func.count(matches.c.id))
            .select_from(ServiceTable)
            .outerjoin(matches, matches.c.service_id == col(ServiceTable.id))
            .where(
                col(ServiceTable.id) == service_id,
                col(ServiceTable.is_active).is_(True),
            )
            .group_by(col(ServiceTable.id))
        )
        count = await self.uow.execute(stmt)
        total = count.scalar_one_or_none()
        page = None
        if total is not None:
            items: list[PublicCatalog] = []
            if offset < total:
                stmt = (
                    query.order_by(col(table.priority), col(table.id))
                    .limit(limit)
                    .offset(offset)
                )
                result = await self.uow.execute(stmt)
                items = [PublicCatalog(*row) for row in result.tuples()]
            page = PagedType(items=items, total_items=total)
        return page
