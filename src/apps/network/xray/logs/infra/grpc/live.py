"""Borrow one cancellable RPC over the application's authenticated channel."""

from asyncio import timeout
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from anyio import CapacityLimiter, WouldBlock
from grpc import StatusCode
from grpc.aio import AioRpcError, UnaryStreamCall

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.enums.live import XrayLogEnd
from ...domain.results.live import XrayLogEvent, XrayLogFeed
from .codec import decode_line
from .v1 import logs_pb2 as wire
from .v1.logs_pb2_grpc import XrayLogsServiceStub

_STATUS = {
    StatusCode.NOT_FOUND: XrayLogEnd.NOT_FOUND,
    StatusCode.FAILED_PRECONDITION: XrayLogEnd.NOT_RUNNING,
    StatusCode.RESOURCE_EXHAUSTED: XrayLogEnd.BUSY,
    StatusCode.DEADLINE_EXCEEDED: XrayLogEnd.TIMEOUT,
    StatusCode.UNAVAILABLE: XrayLogEnd.UNAVAILABLE,
    StatusCode.UNIMPLEMENTED: XrayLogEnd.UNSUPPORTED,
    StatusCode.UNAUTHENTICATED: XrayLogEnd.REJECTED,
    StatusCode.PERMISSION_DENIED: XrayLogEnd.REJECTED,
}
_MAX_STREAMS = 32
_OPEN_TIMEOUT = 2
_STREAM_TIMEOUT = 600

type XrayLogCall = UnaryStreamCall[wire.XrayLogsRequest, wire.XrayLogEvent]


async def _await_admission(call: XrayLogCall) -> XrayLogEnd | None:
    end = None
    try:
        async with timeout(_OPEN_TIMEOUT):
            await call.initial_metadata()
            if call.done():
                code = await call.code()
                if code != StatusCode.OK:
                    end = _STATUS.get(code, XrayLogEnd.INTERRUPTED)
    except TimeoutError:
        end = XrayLogEnd.TIMEOUT
    except AioRpcError as error:
        end = _STATUS.get(error.code(), XrayLogEnd.INTERRUPTED)
    return end


async def _read(call: XrayLogCall) -> AsyncIterator[XrayLogEvent]:
    end = XrayLogEnd.ENDED
    previous = None
    try:
        async for event in call:
            yield XrayLogEvent(line=decode_line(event, previous))
            previous = event.sequence
    except AioRpcError as error:
        end = _STATUS.get(error.code(), XrayLogEnd.INTERRUPTED)
    yield XrayLogEvent(end=end)


class XrayLogsGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels
        self.capacity = CapacityLimiter(_MAX_STREAMS)

    @asynccontextmanager
    async def follow(
        self, node: NodeModel, instance_id: str
    ) -> AsyncIterator[XrayLogFeed]:
        """Reserve one stream with no queue and cancel only its own call.

        Args:
            node: Materialized registry record matching the management target.
            instance_id: Native Xray instance identity.

        Yields:
            One bounded live feed, or the terminal admission outcome.
        """
        channel = await self.channels.get(node.endpoint())
        if channel is None:
            yield XrayLogFeed(end=XrayLogEnd.NOT_CONFIGURED)
        else:
            borrower = object()
            try:
                self.capacity.acquire_on_behalf_of_nowait(borrower)
            except WouldBlock:
                yield XrayLogFeed(end=XrayLogEnd.BUSY)
            else:
                try:
                    call = XrayLogsServiceStub(channel).GetLogs(
                        wire.XrayLogsRequest(id=instance_id),
                        timeout=_STREAM_TIMEOUT,
                    )
                    try:
                        end = await _await_admission(call)
                        yield (
                            XrayLogFeed(end=end)
                            if end is not None
                            else XrayLogFeed(events=_read(call))
                        )
                    finally:
                        call.cancel()
                finally:
                    self.capacity.release_on_behalf_of(borrower)
