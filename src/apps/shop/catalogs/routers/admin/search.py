"""Catalog search and current text-scoped filter metadata."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta, SortMeta

from src.apps.core.auth.routers.dependencies.authorization import require_admin
from src.apps.shop.catalogs.app.interfaces.queries import ICatalogSearchQuery
from src.apps.shop.catalogs.domain.dtos.search import CatalogSearch
from src.apps.shop.catalogs.domain.enums.records import CatalogSort
from src.apps.shop.catalogs.routers.schemas.records import CatalogOutput
from src.apps.shop.catalogs.routers.schemas.search import CatalogMeta, filters

router = APIRouter(
    prefix="/admin/catalogs",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.get("")
async def get_catalogs(
    data: Annotated[CatalogSearch, Query()],
    query: FromDishka[ICatalogSearchQuery],
) -> APIResponse[CatalogOutput, CatalogMeta]:
    page = await query.search(data)
    options = await query.get_options(data)
    return APIResponse[CatalogOutput, CatalogMeta](
        success=True,
        data=CatalogOutput.from_objs(page.items),
        meta=CatalogMeta(
            pager=PagerMeta.from_total(
                data.page, data.per_page, page.total_items
            ),
            filters=filters(options),
            sorts=SortMeta.of(CatalogSort),
        ),
    )
