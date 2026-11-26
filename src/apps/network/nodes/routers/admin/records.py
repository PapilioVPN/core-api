"""Register and inspect managed nodes from the administrator panel."""

from datetime import datetime, timedelta
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType
from papilio.utils.dates import utc_now

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.services import INodeService
from ...config import NodeHostConfig
from ...domain.dtos.records import NodeCreate, NodeList, NodeUpdate
from ..schemas.records import NodeOutput

router = APIRouter(
    prefix="/admin/nodes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


def _stale_before(config: NodeHostConfig) -> datetime:
    return utc_now() - timedelta(seconds=config.checks.stale_after_seconds)


@router.post("", status_code=201)
async def post_node(
    data: NodeCreate,
    nodes: FromDishka[INodeService],
    config: FromDishka[NodeHostConfig],
) -> APIResponse[NodeOutput, None]:
    node = await nodes.create(data)
    output = NodeOutput.from_record(node, stale_before=_stale_before(config))
    return APIResponse[NodeOutput, None].from_data(output)


@router.get("")
async def get_nodes(
    query: Annotated[NodeList, Query()],
    nodes: FromDishka[INodeService],
    config: FromDishka[NodeHostConfig],
) -> APIResponse[NodeOutput, PagerMeta]:
    page = await nodes.list(query)
    stale_before = _stale_before(config)
    return APIResponse[NodeOutput, PagerMeta](
        success=True,
        data=[
            NodeOutput.from_record(node, stale_before=stale_before)
            for node in page.items
        ],
        meta=PagerMeta.from_total(
            query.page, query.per_page, page.total_items
        ),
    )


@router.get("/{id:int}")
async def get_node(
    id: IdType,
    nodes: FromDishka[INodeService],
    config: FromDishka[NodeHostConfig],
) -> APIResponse[NodeOutput, None]:
    node = await nodes.get_by_id(id)
    output = NodeOutput.from_record(node, stale_before=_stale_before(config))
    return APIResponse[NodeOutput, None].from_data(output)


@router.patch("/{id:int}")
async def patch_node(
    id: IdType,
    data: NodeUpdate,
    nodes: FromDishka[INodeService],
    config: FromDishka[NodeHostConfig],
) -> APIResponse[NodeOutput, None]:
    node = await nodes.update(id, data)
    output = NodeOutput.from_record(node, stale_before=_stale_before(config))
    return APIResponse[NodeOutput, None].from_data(output)
