"""Manage catalogs and supply the panel with their selection data."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.schemas.outputs import EnumOut
from papilio.types.aliases import IdType, ListIdType, PerPageType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.shop.products.catalogs.app.interfaces.commands import (
    ICatalogCreateCommand,
    ICatalogUpdateCommand,
)
from src.apps.shop.products.catalogs.app.interfaces.queries import (
    ICatalogFormQuery,
    ICatalogQuery,
)
from src.apps.shop.products.catalogs.app.interfaces.services import (
    ICatalogService,
)
from src.apps.shop.products.catalogs.domain.dtos.records import (
    CatalogCreate,
    CatalogUpdate,
)
from src.apps.shop.products.catalogs.domain.enums.records import (
    CatalogStatus,
)
from src.apps.shop.products.catalogs.routers.schemas.form import (
    CatalogFormOutput,
    ChoicePage,
)
from src.apps.shop.products.catalogs.routers.schemas.records import (
    CatalogDetailOutput,
    CatalogOutput,
)
from src.apps.shop.products.durations.routers.schemas.records import (
    DurationOutput,
)
from src.apps.shop.products.services.routers.schemas.records import (
    ServiceOutput,
)
from src.apps.shop.products.volumes.routers.schemas.records import VolumeOutput

router = APIRouter(
    prefix="/admin/catalogs",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("shop"))],
)


@router.post("", status_code=201)
async def post_catalog(
    data: CatalogCreate, command: FromDishka[ICatalogCreateCommand]
) -> APIResponse[CatalogOutput, None]:
    catalog = await command.create(data)
    output = CatalogOutput.from_obj(catalog)
    return APIResponse[CatalogOutput, None].from_data(output)


@router.get("/form")
async def get_catalog_form(
    query: FromDishka[ICatalogFormQuery], per_page: PerPageType = 20
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


@router.get("/batch")
async def get_catalogs_batch(
    ids: Annotated[ListIdType, Query()], query: FromDishka[ICatalogQuery]
) -> APIResponse[CatalogDetailOutput, None]:
    details = await query.get_by_ids(ids)
    return APIResponse[CatalogDetailOutput, None].from_data(
        CatalogDetailOutput.from_objs(details)
    )


@router.get("/{id:int}")
async def get_catalog(
    id: IdType, query: FromDishka[ICatalogQuery]
) -> APIResponse[CatalogDetailOutput, None]:
    detail = await query.get_by_id(id)
    output = CatalogDetailOutput.from_obj(detail)
    return APIResponse[CatalogDetailOutput, None].from_data(output)


@router.patch("/{id:int}")
async def patch_catalog(
    id: IdType, data: CatalogUpdate, command: FromDishka[ICatalogUpdateCommand]
) -> APIResponse[CatalogOutput, None]:
    catalog = await command.update(id, data)
    output = CatalogOutput.from_obj(catalog)
    return APIResponse[CatalogOutput, None].from_data(output)


@router.delete("/{id:int}")
async def delete_catalog(
    id: IdType, catalogs: FromDishka[ICatalogService]
) -> APIResponse[CatalogOutput, None]:
    catalog = await catalogs.remove(id)
    return APIResponse[CatalogOutput, None].from_data(
        CatalogOutput.from_obj(catalog)
    )
