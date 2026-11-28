"""Register and browse immutable Xray configurations from the Panel."""

from http import HTTPStatus
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, Response
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.errors.outputs import BaseErrorOut
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.records import (
    IXrayRevisionInboundsQuery,
    IXrayRevisionSelectionQuery,
    IXrayRevisionService,
)
from ...domain.dtos.records import (
    XrayRevisionCreate,
    XrayRevisionList,
    XrayRevisionSelectionInput,
)
from ...domain.enums.inbounds import XrayRevisionInboundFailure
from ..schemas.records import (
    XrayRevisionChoiceOutput,
    XrayRevisionInboundOutput,
    XrayRevisionOutput,
    XrayRevisionSelectionMeta,
)

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
    if saved is None:
        response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        body = APIResponse[XrayRevisionOutput, None](
            success=False,
            error=BaseErrorOut(
                message="The Xray revision source is unavailable.",
                message_code="xray_revision_source_unavailable",
            ),
        )
    else:
        if not saved.created:
            response.status_code = HTTPStatus.OK
        output = XrayRevisionOutput.from_obj(saved.revision)
        body = APIResponse[XrayRevisionOutput, None].from_data(output)
    return body


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


@router.get("/{id:int}/inbounds")
async def get_revision_inbounds(
    id: IdType,
    response: Response,
    query: FromDishka[IXrayRevisionInboundsQuery],
) -> APIResponse[XrayRevisionInboundOutput, None]:
    selected = await query.get(id)
    response.headers["Cache-Control"] = "private, no-store"
    if selected.failure is None:
        body = APIResponse[XrayRevisionInboundOutput, None].from_data(
            XrayRevisionInboundOutput.from_objs(selected.items)
        )
    else:
        if selected.failure is XrayRevisionInboundFailure.SOURCE_UNAVAILABLE:
            response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
            message = "The Xray revision source is unavailable."
            message_code = "xray_revision_source_unavailable"
        else:
            response.status_code = HTTPStatus.UNPROCESSABLE_ENTITY
            message = "The Xray revision has invalid or duplicate inbounds."
            message_code = selected.failure.value
        body = APIResponse[XrayRevisionInboundOutput, None](
            success=False,
            error=BaseErrorOut(message=message, message_code=message_code),
        )
    return body


@router.get("/simple")
async def get_revision_choices(
    data: Annotated[XrayRevisionSelectionInput, Query()],
    response: Response,
    query: FromDishka[IXrayRevisionSelectionQuery],
) -> APIResponse[XrayRevisionChoiceOutput, XrayRevisionSelectionMeta]:
    selected = await query.get(data)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[XrayRevisionChoiceOutput, XrayRevisionSelectionMeta](
        success=True,
        data=XrayRevisionChoiceOutput.from_objs(selected.items),
        meta=XrayRevisionSelectionMeta(next_before_id=selected.next_before_id),
    )
