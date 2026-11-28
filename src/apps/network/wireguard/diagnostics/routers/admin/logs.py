"""Stream WireGuard logs to authorized Panel operators."""

from collections.abc import AsyncIterator
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, Depends, Response
from fastapi.sse import EventSourceResponse, ServerSentEvent
from papilio.types.aliases import IdType

from src.apps.core.access.auth.routers.dependencies.authorization import (
    require_admin,
)
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.observations.routers.streams import (
    log_events,
)
from src.apps.network.wireguard.interfaces.domain.dtos.identity import (
    WireGuardInterfaceName,
)

from ...app.interfaces.logs import IWireGuardLogsQuery
from ...domain.results.logs import WireGuardLogEvent
from ..schemas.logs import WireGuardLogEventOutput, WireGuardLogReadyOutput

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/wireguard/interfaces/{name}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@inject
async def _open_feed(
    node_id: IdType,
    name: WireGuardInterfaceName,
    query: FromDishka[IWireGuardLogsQuery],
    response: Response,
) -> AsyncIterator[LogStream[WireGuardLogEvent]]:
    response.headers["Cache-Control"] = "private, no-store"
    async with query.follow(node_id, name) as feed:
        yield feed


@router.get("/logs", response_class=EventSourceResponse)
async def follow_logs(
    node_id: IdType,
    name: WireGuardInterfaceName,
    feed: Annotated[LogStream[WireGuardLogEvent], Depends(_open_feed)],
) -> AsyncIterator[ServerSentEvent]:
    ready = WireGuardLogReadyOutput(node_id=node_id, name=name)
    async for event in log_events(
        feed, ready, WireGuardLogEventOutput.from_obj
    ):
        yield event
