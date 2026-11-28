"""Persist the display order requested by an authorized operator."""

from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.records import IXrayRevisionService
from ...domain.dtos.records import XrayRevisionOrderInput

router = APIRouter(
    prefix="/admin/xray/revisions",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.put("/order", status_code=HTTPStatus.NO_CONTENT)
async def put_revision_order(
    data: XrayRevisionOrderInput,
    revisions: FromDishka[IXrayRevisionService],
) -> Response:
    await revisions.reorder(data)
    return Response(status_code=HTTPStatus.NO_CONTENT)
