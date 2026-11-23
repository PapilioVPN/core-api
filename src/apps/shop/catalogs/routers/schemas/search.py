"""Variant-style pagination, facets and sorts for catalog search."""

from typing import Literal

from papilio.api.responses.meta import FilterMeta, PagerMeta, SortMeta
from papilio.schemas.outputs import BaseOutput
from papilio.types.enums import FilterType
from pydantic import Field

from src.apps.shop.catalogs.domain.results.filters import CatalogOptions


class OptionOutput(BaseOutput):
    id: int | str | bool
    label: str
    count: int


class FacetOutput(FilterMeta[OptionOutput]):
    key: Literal["service_id", "status", "is_unlimited", "has_expiry"]
    id: int | None = Field(default=None, exclude=True)
    type: FilterType = FilterType.RADIO


class PriceOutput(BaseOutput):
    key: Literal["price"] = "price"
    title: str = "قیمت (ریال)"
    type: Literal[FilterType.SLIDER] = FilterType.SLIDER
    minimum: int | None
    maximum: int | None


class CatalogMeta(BaseOutput):
    pager: PagerMeta
    filters: list[FacetOutput | PriceOutput]
    sorts: SortMeta


def filters(options: CatalogOptions) -> list[FacetOutput | PriceOutput]:
    """Expose active search choices and inclusive integer price bounds."""
    return [
        FacetOutput(
            key="service_id",
            title="سرویس",
            options=OptionOutput.from_objs(options.services),
        ),
        FacetOutput(
            key="status",
            title="وضعیت",
            options=OptionOutput.from_objs(options.statuses),
        ),
        FacetOutput(
            key="is_unlimited",
            title="نوع حجم",
            options=OptionOutput.from_objs(options.volumes),
        ),
        FacetOutput(
            key="has_expiry",
            title="مدت اعتبار",
            options=OptionOutput.from_objs(options.expiries),
        ),
        PriceOutput(minimum=options.min_price, maximum=options.max_price),
    ]
