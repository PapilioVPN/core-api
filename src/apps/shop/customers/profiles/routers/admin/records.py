"""Register, read and edit customer profiles from the panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.types.aliases import IdType, ListIdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.services import ICustomerService
from ...domain.dtos.records import ProfileCreate, ProfileUpdate
from ..schemas.records import ProfileOutput

router = APIRouter(
    prefix="/admin/customers",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("customers"))],
)


@router.post("", status_code=201)
async def post_customer(
    data: ProfileCreate, profiles: FromDishka[ICustomerService]
) -> APIResponse[ProfileOutput, None]:
    profile = await profiles.create(data)
    return APIResponse[ProfileOutput, None].from_data(
        ProfileOutput.from_obj(profile)
    )


@router.get("/batch")
async def get_customers_batch(
    ids: Annotated[ListIdType, Query()], profiles: FromDishka[ICustomerService]
) -> APIResponse[ProfileOutput, None]:
    rows = await profiles.get_by_ids(ids)
    return APIResponse[ProfileOutput, None].from_data(
        ProfileOutput.from_objs(rows)
    )


@router.get("/{id:int}")
async def get_customer(
    id: IdType, profiles: FromDishka[ICustomerService]
) -> APIResponse[ProfileOutput, None]:
    profile = await profiles.get_by_id(id)
    return APIResponse[ProfileOutput, None].from_data(
        ProfileOutput.from_obj(profile)
    )


@router.patch("/{id:int}")
async def patch_customer(
    id: IdType, data: ProfileUpdate, profiles: FromDishka[ICustomerService]
) -> APIResponse[ProfileOutput, None]:
    profile = await profiles.update(id, data)
    return APIResponse[ProfileOutput, None].from_data(
        ProfileOutput.from_obj(profile)
    )
