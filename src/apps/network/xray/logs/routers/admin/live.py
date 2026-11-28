"""Serve operator-only Xray logs as native FastAPI Server-Sent Events."""

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
    InstanceLogReadyOutput,
    log_events,
)
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.live import IXrayLogsQuery
from ...domain.results.live import XrayLogLine
from ..schemas.live import XrayLogLineOutput

router = APIRouter(
    prefix="/admin/nodes/{node_id:int}/xray/instances/{instance_id}",
    route_class=DishkaRoute,
    dependencies=[Depends(require_admin("network"))],
)


@inject
async def _open_feed(
    node_id: IdType,
    instance_id: XrayInstanceID,
    query: FromDishka[IXrayLogsQuery],
    response: Response,
) -> AsyncIterator[LogStream[XrayLogLine]]:
    response.headers["Cache-Control"] = "private, no-store"
    async with query.follow(node_id, instance_id) as feed:
        yield feed


@router.get("/logs", response_class=EventSourceResponse)
async def follow_logs(
    node_id: IdType,
    instance_id: XrayInstanceID,
    feed: Annotated[LogStream[XrayLogLine], Depends(_open_feed)],
) -> AsyncIterator[ServerSentEvent]:
    ready = InstanceLogReadyOutput(node_id=node_id, instance_id=instance_id)
    async for event in log_events(feed, ready, XrayLogLineOutput.from_line):
        yield event
