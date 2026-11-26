"""Register and browse immutable Xray configurations from the Panel."""

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, Response
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.revisions import IXrayRevisionService
from ...domain.dtos.revisions import XrayRevisionCreate, XrayRevisionList
from ..schemas.revisions import XrayRevisionOutput

router = APIRouter(
    prefix="/admin/xray/revisions",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.post("", status_code=201)
async def post_revision(
    data: XrayRevisionCreate,
    response: Response,
    revisions: FromDishka[IXrayRevisionService],
) -> APIResponse[XrayRevisionOutput, None]:
    saved = await revisions.save(data)
    if not saved.created:
        response.status_code = 200
    output = XrayRevisionOutput.from_obj(saved.revision)
    return APIResponse[XrayRevisionOutput, None].from_data(output)


@router.get("")
async def get_revisions(
    data: Annotated[XrayRevisionList, Query()],
    revisions: FromDishka[IXrayRevisionService],
) -> APIResponse[XrayRevisionOutput, PagerMeta]:
    page = await revisions.list(data)
    return APIResponse[XrayRevisionOutput, PagerMeta](
        success=True,
        data=XrayRevisionOutput.from_objs(page.items),
        meta=PagerMeta.from_total(data.page, data.per_page, page.total_items),
    )


@router.get("/{id:int}")
async def get_revision(
    id: IdType, revisions: FromDishka[IXrayRevisionService]
) -> APIResponse[XrayRevisionOutput, None]:
    revision = await revisions.get_by_id(id)
    output = XrayRevisionOutput.from_obj(revision)
    return APIResponse[XrayRevisionOutput, None].from_data(output)
