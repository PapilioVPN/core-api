"""Register and inspect managed nodes from the administrator panel."""

from datetime import datetime, timedelta
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, Response
from papilio.api.responses.envelope import APIResponse
from papilio.api.responses.meta import PagerMeta
from papilio.types.aliases import IdType
from papilio.utils.dates import utc_now

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)

from ...app.interfaces.selection import INodeSelectionQuery
from ...app.interfaces.services import INodeService
from ...app.interfaces.state import INodeStateCommand
from ...domain.dtos.records import (
    NodeCreate,
    NodeList,
    NodeSelectionInput,
    NodeStateInput,
    NodeUpdate,
)
from ..schemas.records import (
    NodeChoiceOutput,
    NodeOutput,
    NodeSelectionMeta,
    NodeStateOutput,
)

router = APIRouter(
    prefix="/admin/nodes",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)

_STALE_AFTER = timedelta(seconds=180)


def _stale_before() -> datetime:
    return utc_now() - _STALE_AFTER


@router.post("", status_code=201)
async def post_node(
    data: NodeCreate,
    nodes: FromDishka[INodeService],
) -> APIResponse[NodeOutput, None]:
    node = await nodes.create(data)
    output = NodeOutput.from_record(node, stale_before=_stale_before())
    return APIResponse[NodeOutput, None].from_data(output)


@router.get("")
async def get_nodes(
    query: Annotated[NodeList, Query()],
    nodes: FromDishka[INodeService],
) -> APIResponse[NodeOutput, PagerMeta]:
    page = await nodes.list(query)
    stale_before = _stale_before()
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
) -> APIResponse[NodeOutput, None]:
    node = await nodes.get_by_id(id)
    output = NodeOutput.from_record(node, stale_before=_stale_before())
    return APIResponse[NodeOutput, None].from_data(output)


@router.get("/simple")
async def get_node_choices(
    data: Annotated[NodeSelectionInput, Query()],
    response: Response,
    query: FromDishka[INodeSelectionQuery],
) -> APIResponse[NodeChoiceOutput, NodeSelectionMeta]:
    page = await query.get(data)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[NodeChoiceOutput, NodeSelectionMeta](
        success=True,
        data=NodeChoiceOutput.from_objs(page.items),
        meta=NodeSelectionMeta(next_before_id=page.next_before_id),
    )


@router.patch("/state")
async def set_node_states(
    data: NodeStateInput,
    response: Response,
    command: FromDishka[INodeStateCommand],
) -> APIResponse[NodeStateOutput, None]:
    results = await command.set_enabled(data)
    response.headers["Cache-Control"] = "private, no-store"
    return APIResponse[NodeStateOutput, None].from_data(
        NodeStateOutput.from_objs(results)
    )


@router.patch("/{id:int}")
async def patch_node(
    id: IdType,
    data: NodeUpdate,
    nodes: FromDishka[INodeService],
) -> APIResponse[NodeOutput, None]:
    node = await nodes.update(id, data)
    output = NodeOutput.from_record(node, stale_before=_stale_before())
    return APIResponse[NodeOutput, None].from_data(output)
