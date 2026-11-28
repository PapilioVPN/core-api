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
from src.apps.network.xray.instances.domain.dtos.identity import XrayInstanceID

from ...app.interfaces.live import IXrayLogsQuery
from ...domain.enums.live import XrayLogEnd
from ...domain.results.live import XrayLogFeed
from ..schemas.live import (
    XrayLogEndOutput,
    XrayLogLineOutput,
    XrayLogReadyOutput,
)

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
) -> AsyncIterator[XrayLogFeed | XrayLogEnd]:
    response.headers["Cache-Control"] = "private, no-store"
    async with query.follow(node_id, instance_id) as feed:
        yield feed


@router.get("/logs", response_class=EventSourceResponse)
async def follow_logs(
    node_id: IdType,
    instance_id: XrayInstanceID,
    feed: Annotated[XrayLogFeed | XrayLogEnd, Depends(_open_feed)],
) -> AsyncIterator[ServerSentEvent]:
    if isinstance(feed, XrayLogEnd):
        yield ServerSentEvent(event="end", data=XrayLogEndOutput(status=feed))
    else:
        yield ServerSentEvent(
            event="ready",
            data=XrayLogReadyOutput(node_id=node_id, instance_id=instance_id),
        )
        async for item in feed:
            if isinstance(item, XrayLogEnd):
                yield ServerSentEvent(
                    event="end", data=XrayLogEndOutput(status=item)
                )
            else:
                yield ServerSentEvent(
                    event="log", data=XrayLogLineOutput.from_line(item)
                )
