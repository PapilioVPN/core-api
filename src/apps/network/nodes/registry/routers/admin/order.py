"""Persist the display order selected by a network operator."""

from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Response

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.services import INodeService
from ...domain.dtos.records import NodeOrderInput

router = APIRouter(
    prefix="/admin/nodes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@router.put("/order", status_code=HTTPStatus.NO_CONTENT)
async def put_node_order(
    data: NodeOrderInput, nodes: FromDishka[INodeService]
) -> Response:
    await nodes.reorder(data)
    return Response(status_code=HTTPStatus.NO_CONTENT)
