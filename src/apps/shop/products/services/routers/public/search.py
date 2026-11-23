"""Public storefront routes for services."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta

from src.apps.shop.products.services.app.interfaces.public import (
    IPublicServiceQuery,
)
from src.apps.shop.products.services.domain.dtos.public import (
    PublicServiceSearch,
)
from src.apps.shop.products.services.routers.schemas.public import (
    PublicServiceOutput,
)

router = APIRouter(prefix="/public/services", route_class=DishkaRoute)


@router.get("")
async def get_services(
    data: Annotated[PublicServiceSearch, Query()],
    query: FromDishka[IPublicServiceQuery],
) -> APIResponse[PublicServiceOutput, PagerMeta]:
    """Search the services available in the storefront.

    Args:
        data: Validated title search and paging inputs.
        query: Public service search contract.

    Returns:
        Public service cards with native pagination metadata.
    """
    page = await query.search(data)
    return APIResponse[PublicServiceOutput, PagerMeta](
        success=True,
        data=PublicServiceOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )
