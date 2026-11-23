"""Manage catalogs and supply the panel with their selection data."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta, SortMeta
from papilio.schemas.outputs import EnumOut
from papilio.types.aliases import IdType, PerPageType

from src.apps.core.auth.routers.dependencies.authorization import require_admin
from src.apps.shop.catalogs.app.interfaces.commands import ICatalogCommand
from src.apps.shop.catalogs.app.interfaces.queries import ICatalogQuery
from src.apps.shop.catalogs.domain.dtos.records import (
    CatalogCreate,
    CatalogUpdate,
)
from src.apps.shop.catalogs.domain.dtos.search import CatalogSearch
from src.apps.shop.catalogs.domain.enums.records import (
    CatalogSort,
    CatalogStatus,
)
from src.apps.shop.catalogs.routers.schemas.form import (
    CatalogFormOutput,
    ChoicePage,
)
from src.apps.shop.catalogs.routers.schemas.records import (
    CatalogDetailOutput,
    CatalogOutput,
)
from src.apps.shop.catalogs.routers.schemas.search import CatalogMeta, filters
from src.apps.shop.durations.routers.schemas.records import DurationOutput
from src.apps.shop.services.routers.schemas.records import ServiceOutput
from src.apps.shop.volumes.routers.schemas.records import VolumeOutput

router = APIRouter(
    prefix="/admin/catalogs",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_catalog(
    data: CatalogCreate, command: FromDishka[ICatalogCommand]
) -> APIResponse[CatalogOutput, None]:
    catalog = await command.create(data)
    output = CatalogOutput.from_obj(catalog)
    return APIResponse[CatalogOutput, None].from_data(output)


@router.get("")
async def get_catalogs(
    data: Annotated[CatalogSearch, Query()],
    query: FromDishka[ICatalogQuery],
) -> APIResponse[CatalogOutput, CatalogMeta]:
    page = await query.list(data)
    options = await query.options(data)
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


@router.get("/form")
async def get_catalog_form(
    query: FromDishka[ICatalogQuery], per_page: PerPageType = 20
) -> APIResponse[CatalogFormOutput, None]:
    form = await query.form(per_page)
    output = CatalogFormOutput(
        services=ChoicePage[ServiceOutput].from_obj(form.services),
        volumes=ChoicePage[VolumeOutput].from_obj(form.volumes),
        durations=ChoicePage[DurationOutput].from_obj(form.durations),
        per_page=per_page,
        statuses=EnumOut.of(CatalogStatus),
    )
    return APIResponse[CatalogFormOutput, None].from_data(output)


@router.get("/{id:int}")
async def get_catalog(
    id: IdType, query: FromDishka[ICatalogQuery]
) -> APIResponse[CatalogDetailOutput, None]:
    detail = await query.get_by_id(id)
    output = CatalogDetailOutput.from_obj(detail)
    return APIResponse[CatalogDetailOutput, None].from_data(output)


@router.patch("/{id:int}")
async def patch_catalog(
    id: IdType, data: CatalogUpdate, command: FromDishka[ICatalogCommand]
) -> APIResponse[CatalogOutput, None]:
    catalog = await command.update(id, data)
    output = CatalogOutput.from_obj(catalog)
    return APIResponse[CatalogOutput, None].from_data(output)
