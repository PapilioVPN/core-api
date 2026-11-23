"""Configure customer groups from the panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType, ListIdType, SlugType

from src.apps.core.auth.routers.dependencies.authorization import require_admin

from ...app.interfaces.services import IGroupCRUD
from ...domain.dtos.records import GroupCreate, GroupList, GroupUpdate
from ..schemas.records import GroupOutput

router = APIRouter(
    prefix="/admin/customer-groups",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("customers"))],
)


@router.post("", status_code=201)
async def post_group(
    data: GroupCreate, groups: FromDishka[IGroupCRUD]
) -> APIResponse[GroupOutput, None]:
    group = await groups.create(data)
    return APIResponse[GroupOutput, None].from_data(
        GroupOutput.from_obj(group)
    )


@router.get("")
async def get_groups(
    query: Annotated[GroupList, Query()], groups: FromDishka[IGroupCRUD]
) -> APIResponse[GroupOutput, PagerMeta]:
    page = await groups.list(query)
    return APIResponse[GroupOutput, PagerMeta](
        success=True,
        data=GroupOutput.from_objs(page.items),
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/batch")
async def get_groups_batch(
    ids: Annotated[ListIdType, Query()], groups: FromDishka[IGroupCRUD]
) -> APIResponse[GroupOutput, None]:
    rows = await groups.get_by_ids(ids)
    return APIResponse[GroupOutput, None].from_data(
        GroupOutput.from_objs(rows)
    )


@router.get("/key/{key}")
async def get_group_by_key(
    key: SlugType, groups: FromDishka[IGroupCRUD]
) -> APIResponse[GroupOutput, None]:
    group = await groups.get_by_key(key)
    return APIResponse[GroupOutput, None].from_data(
        GroupOutput.from_obj(group)
    )


@router.get("/{id:int}")
async def get_group(
    id: IdType, groups: FromDishka[IGroupCRUD]
) -> APIResponse[GroupOutput, None]:
    group = await groups.get_by_id(id)
    return APIResponse[GroupOutput, None].from_data(
        GroupOutput.from_obj(group)
    )


@router.patch("/{id:int}")
async def patch_group(
    id: IdType, data: GroupUpdate, groups: FromDishka[IGroupCRUD]
) -> APIResponse[GroupOutput, None]:
    group = await groups.update(id, data)
    return APIResponse[GroupOutput, None].from_data(
        GroupOutput.from_obj(group)
    )


@router.delete("/{id:int}")
async def delete_group(
    id: IdType, groups: FromDishka[IGroupCRUD]
) -> APIResponse[GroupOutput, None]:
    group = await groups.remove(id)
    return APIResponse[GroupOutput, None].from_data(
        GroupOutput.from_obj(group)
    )
