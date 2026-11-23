"""Expose current volume and duration choices to the storefront."""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, PageType, PerPageType

from src.apps.shop.products.volume_ranges.app.interfaces.queries import (
    IPublicRangeQuery,
)
from src.apps.shop.products.volume_ranges.routers.schemas.records import (
    RangeOutput,
)

router = APIRouter(
    prefix="/public/services/{service_id:int}/volume-ranges",
    route_class=DishkaRoute,
)


@router.get("")
async def get_ranges(
    service_id: IdType,
    query: FromDishka[IPublicRangeQuery],
    page: PageType = 1,
    per_page: PerPageType = 20,
) -> APIResponse[RangeOutput, PagerMeta]:
    """Read an active service's volume and duration choices.

    Args:
        service_id: Validated parent identity.
        query: Public range query.
        page: Requested page.
        per_page: Maximum number of ranges in that page.

    Returns:
        The current choices and native pagination metadata.
    """
    rows = await query.list(service_id, page=page, per_page=per_page)
    return APIResponse[RangeOutput, PagerMeta](
        success=True,
        data=RangeOutput.from_objs(rows.items),
        meta=PagerMeta.from_total(page, per_page, rows.total_items),
    )
