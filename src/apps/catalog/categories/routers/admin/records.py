"""Manage catalog categories from the panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.catalog.categories.app.services.records import CategoryService
from src.apps.catalog.categories.domain.dtos.records import (
    CategoryCreate,
    CategoryList,
    CategoryUpdate,
)
from src.apps.catalog.categories.routers.schemas.records import CategoryOutput
from src.apps.core.auth.routers.dependencies.authorization import require_admin

router = APIRouter(
    prefix="/admin/categories",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("catalog"))],
)


@router.post("", status_code=201)
async def post_category(
    data: CategoryCreate, service: FromDishka[CategoryService]
) -> APIResponse[CategoryOutput, None]:
    category = await service.create(data)
    output = CategoryOutput.from_obj(category)
    return APIResponse[CategoryOutput, None].from_data(output)


@router.get("")
async def get_categories(
    query: Annotated[CategoryList, Query()],
    service: FromDishka[CategoryService],
) -> APIResponse[CategoryOutput, PagerMeta]:
    page = await service.list(query)
    return APIResponse[CategoryOutput, PagerMeta](
        success=True,
        data=CategoryOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id}")
async def get_category(
    id: IdType, service: FromDishka[CategoryService]
) -> APIResponse[CategoryOutput, None]:
    category = await service.get_by_id(id)
    output = CategoryOutput.from_obj(category)
    return APIResponse[CategoryOutput, None].from_data(output)


@router.patch("/{id}")
async def patch_category(
    id: IdType,
    data: CategoryUpdate,
    service: FromDishka[CategoryService],
) -> APIResponse[CategoryOutput, None]:
    category = await service.update(id, data)
    output = CategoryOutput.from_obj(category)
    return APIResponse[CategoryOutput, None].from_data(output)
