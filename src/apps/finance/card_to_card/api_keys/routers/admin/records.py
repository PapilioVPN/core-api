"""Manage card transfer webhook credentials from the Finance panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, Response
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.services import IAPIKeyService
from ...domain.dtos.records import APIKeyCreate, APIKeyList
from ..schemas.records import APIKeyIssuedOutput, APIKeyOutput

router = APIRouter(
    prefix="/admin/card-to-card/api-keys",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("finance"))],
)


@router.post("", status_code=201)
async def post_key(
    data: APIKeyCreate,
    response: Response,
    service: FromDishka[IAPIKeyService],
) -> APIResponse[APIKeyIssuedOutput, None]:
    issued = await service.create(data)
    response.headers["Cache-Control"] = "no-store"
    output = APIKeyIssuedOutput.from_obj(issued)
    return APIResponse[APIKeyIssuedOutput, None].from_data(output)


@router.get("")
async def get_keys(
    query: Annotated[APIKeyList, Query()],
    service: FromDishka[IAPIKeyService],
) -> APIResponse[APIKeyOutput, PagerMeta]:
    page = await service.list(query)
    return APIResponse[APIKeyOutput, PagerMeta](
        success=True,
        data=APIKeyOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id:int}")
async def get_key(
    id: IdType, service: FromDishka[IAPIKeyService]
) -> APIResponse[APIKeyOutput, None]:
    record = await service.get_by_id(id)
    output = APIKeyOutput.from_obj(record)
    return APIResponse[APIKeyOutput, None].from_data(output)


@router.patch("/{id:int}/revoke")
async def revoke_key(
    id: IdType, service: FromDishka[IAPIKeyService]
) -> APIResponse[APIKeyOutput, None]:
    record = await service.revoke(id)
    output = APIKeyOutput.from_obj(record)
    return APIResponse[APIKeyOutput, None].from_data(output)
