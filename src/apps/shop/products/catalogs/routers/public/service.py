"""Expose catalog search under a selected public service."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.shop.products.catalogs.app.interfaces.public import (
    IServiceCatalogQuery,
)
from src.apps.shop.products.catalogs.domain.dtos.public import (
    ServiceCatalogSearch,
)
from src.apps.shop.products.catalogs.routers.schemas.public import (
    PublicCatalogOutput,
)

router = APIRouter(prefix="/public/services", route_class=DishkaRoute)


@router.get("/{service_id:int}/catalogs")
async def get_service_catalogs(
    service_id: IdType,
    data: Annotated[ServiceCatalogSearch, Query()],
    query: FromDishka[IServiceCatalogQuery],
) -> APIResponse[PublicCatalogOutput, PagerMeta]:
    """Search published offers that belong to the selected service.

    Args:
        service_id: Validated parent service identity.
        data: Validated offer filters and page selection.
        query: Service-scoped catalog search contract.

    Returns:
        The requested page with its matching total and native paging metadata.

    Raises:
        NotFoundException: The parent service is absent or inactive.
    """
    page = await query.search(service_id, data)
    return APIResponse[PublicCatalogOutput, PagerMeta](
        success=True,
        data=PublicCatalogOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )
