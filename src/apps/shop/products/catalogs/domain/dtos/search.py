"""Validated catalog search, filter and paging inputs."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    IdType,
    PageType,
    PerPageType,
    RialType,
    ValueType,
)
from papilio.types.enums import SortOrder

from src.apps.shop.products.catalogs.domain.enums.records import (
    CatalogSort,
    CatalogStatus,
)


class CatalogSearch(BaseDTO):
    q: ValueType | None = None
    service_id: IdType | None = None
    status: CatalogStatus | None = None
    is_unlimited: bool | None = None
    volume_id: IdType | None = None
    duration_id: IdType | None = None
    has_expiry: bool | None = None
    min_price: RialType | None = None
    max_price: RialType | None = None
    sort_by: CatalogSort = CatalogSort.PRIORITY
    sort_order: SortOrder = SortOrder.ASC
    page: PageType = 1
    per_page: PerPageType = 20
