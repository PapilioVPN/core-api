"""Bound and close each native Node log call independently."""

from asyncio import timeout
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from anyio import CapacityLimiter, WouldBlock
from grpc import StatusCode
from grpc.aio import AioRpcError, Channel, UnaryStreamCall

from src.apps.network.nodes.observations.domain.enums.logs import LogStreamEnd
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint

from .channels import NodeChannels

_MAX_STREAMS = 32
_OPEN_TIMEOUT = 2
_STREAM_TIMEOUT = 600
_STATUS = {
    StatusCode.NOT_FOUND: LogStreamEnd.NOT_FOUND,
    StatusCode.RESOURCE_EXHAUSTED: LogStreamEnd.BUSY,
    StatusCode.DEADLINE_EXCEEDED: LogStreamEnd.TIMEOUT,
    StatusCode.UNAVAILABLE: LogStreamEnd.UNAVAILABLE,
    StatusCode.UNIMPLEMENTED: LogStreamEnd.UNSUPPORTED,
    StatusCode.UNAUTHENTICATED: LogStreamEnd.REJECTED,
    StatusCode.PERMISSION_DENIED: LogStreamEnd.REJECTED,
}


def _rpc_end(
    code: StatusCode, failed_precondition: LogStreamEnd
) -> LogStreamEnd:
    return (
        failed_precondition
        if code == StatusCode.FAILED_PRECONDITION
        else _STATUS.get(code, LogStreamEnd.INTERRUPTED)
    )


async def _await_admission[Request, Reply](
    call: UnaryStreamCall[Request, Reply],
    failed_precondition: LogStreamEnd,
) -> LogStreamEnd | None:
    end = None
    try:
        async with timeout(_OPEN_TIMEOUT):
            await call.initial_metadata()
            if call.done():
                code = await call.code()
                if code != StatusCode.OK:
                    end = _rpc_end(code, failed_precondition)
    except TimeoutError:
        end = LogStreamEnd.TIMEOUT
    except AioRpcError as error:
        end = _rpc_end(error.code(), failed_precondition)
    return end


async def _read[Request, Reply, Entry](
    call: UnaryStreamCall[Request, Reply],
    decode: Callable[[Reply], Entry | None],
    failed_precondition: LogStreamEnd,
) -> AsyncIterator[Entry | LogStreamEnd]:
    end = LogStreamEnd.ENDED
    try:
        async for reply in call:
            entry = decode(reply)
            if entry is None:
                end = LogStreamEnd.INTERRUPTED
                break
            yield entry
    except AioRpcError as error:
        end = _rpc_end(error.code(), failed_precondition)
    yield end


class NodeLogStreams:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels
        self.capacity = CapacityLimiter(_MAX_STREAMS)

    @asynccontextmanager
    async def follow[Request, Reply, Entry](
        self,
        endpoint: NodeEndpoint,
        start: Callable[[Channel, int], UnaryStreamCall[Request, Reply]],
        decode: Callable[[Reply], Entry | None],
        *,
        await_headers: bool = True,
        failed_precondition: LogStreamEnd = LogStreamEnd.NOT_RUNNING,
    ) -> AsyncIterator[LogStream[Entry]]:
        """Borrow one authenticated streaming call with no admission queue.

        Args:
            endpoint: Exact registered Node connection.
            start: Native RPC factory accepting its deadline in seconds.
            decode: Map one native reply to its owner's log observation.
            await_headers: Require early headers from the native handler.
            failed_precondition: Native stream precondition outcome.

        Yields:
            The bounded stream or a typed admission outcome.
        """
        channel = await self.channels.get(endpoint)
        if channel is None:
            yield LogStream(end=LogStreamEnd.NOT_CONFIGURED)
        else:
            borrower = object()
            try:
                self.capacity.acquire_on_behalf_of_nowait(borrower)
            except WouldBlock:
                yield LogStream(end=LogStreamEnd.BUSY)
            else:
                try:
                    call = start(channel, _STREAM_TIMEOUT)
                    try:
                        end = (
                            await _await_admission(call, failed_precondition)
                            if await_headers
                            else None
                        )
                        yield (
                            LogStream(end=end)
                            if end is not None
                            else LogStream(
                                entries=_read(
                                    call, decode, failed_precondition
                                )
                            )
                        )
                    finally:
                        call.cancel()
                finally:
                    self.capacity.release_on_behalf_of(borrower)
