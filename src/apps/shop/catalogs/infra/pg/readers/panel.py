"""Focused PostgreSQL reads for catalog detail and panel search."""

from collections import Counter
from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlmodel import col

from src.apps.shop.catalogs.domain.dtos.search import CatalogSearch
from src.apps.shop.catalogs.domain.enums.records import CatalogStatus
from src.apps.shop.catalogs.domain.models.records import CatalogModel
from src.apps.shop.catalogs.domain.results.details import CatalogDetail
from src.apps.shop.catalogs.domain.results.filters import (
    CatalogOptions,
    Choice,
)
from src.apps.shop.catalogs.infra.pg.sql.details import details
from src.apps.shop.catalogs.infra.pg.sql.search import facets, search
from src.apps.shop.catalogs.infra.pg.tables import CatalogTable


class CatalogReader(PGReader):
    async def get_by_id(self, id: int) -> CatalogDetail | None:
        """Read a catalog and its selected volume and duration in one query.

        Args:
            id: Stored catalog identity.

        Returns:
            The catalog and its actual referenced definitions, or None.
        """
        stmt = details().where(col(CatalogTable.id) == id)
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return CatalogDetail(*row) if row is not None else None

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[CatalogDetail]:
        """Load all existing details for a bounded ID set in one query."""
        stmt = details().where(col(CatalogTable.id).in_(ids))
        result = await self.uow.execute(stmt)
        return [CatalogDetail(*row) for row in result.tuples()]

    async def list(self, data: CatalogSearch) -> PagedType[CatalogModel]:
        """Read a filtered page for the administrator panel.

        Args:
            data: Validated filters, sort selection and page bounds.

        Returns:
            Matching catalogs and their total before pagination.
        """
        page = await fetch_page(
            self.uow,
            search(data),
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
        )
        return page

    async def options(self, q: str | None) -> CatalogOptions:
        """Read filter facets and rial price bounds for text matches.

        Args:
            q: Literal optional search across catalog and service names.

        Returns:
            Counts and price limits before paging and selected filters.
        """
        result = await self.uow.execute(facets(q))
        services: Counter[tuple[int, str]] = Counter()
        statuses: Counter[CatalogStatus] = Counter()
        volumes: Counter[bool] = Counter()
        expiries: Counter[bool] = Counter()
        lows: list[int] = []
        highs: list[int] = []
        for (
            id,
            title,
            status,
            unlimited,
            expiry,
            count,
            low,
            high,
        ) in result.tuples():
            services[id, title] += count
            statuses[status] += count
            volumes[unlimited] += count
            expiries[expiry] += count
            lows.append(low)
            highs.append(high)
        return CatalogOptions(
            services=[
                Choice(id, title, count)
                for (id, title), count in sorted(services.items())
            ],
            statuses=[
                Choice(kind.value, kind.fa, statuses[kind])
                for kind in CatalogStatus
                if kind in statuses
            ],
            volumes=[
                Choice(value, label, volumes[value])
                for value, label in ((True, "نامحدود"), (False, "حجمی"))
                if value in volumes
            ],
            expiries=[
                Choice(value, label, expiries[value])
                for value, label in ((True, "مدت‌دار"), (False, "بدون انقضا"))
                if value in expiries
            ],
            min_price=min(lows) if lows else None,
            max_price=max(highs) if highs else None,
        )
