"""Format authorized native observations as Panel Server-Sent Events."""

from collections.abc import AsyncIterator, Callable

from fastapi.sse import ServerSentEvent
from papilio.schemas.outputs import BaseOutput

from ..domain.enums.logs import LogStreamEnd
from ..domain.results.logs import LogStream


class _LogEndOutput(BaseOutput):
    status: LogStreamEnd


class InstanceLogReadyOutput(BaseOutput):
    node_id: int
    instance_id: str


async def log_events[Entry](
    feed: LogStream[Entry],
    ready: BaseOutput,
    output: Callable[[Entry], BaseOutput],
    *,
    ready_on_open: bool = True,
) -> AsyncIterator[ServerSentEvent]:
    """Emit one ready event, typed log entries and a terminal outcome."""
    if feed.end is not None:
        yield ServerSentEvent(event="end", data=_LogEndOutput(status=feed.end))
    elif feed.entries is not None:
        if ready_on_open:
            yield ServerSentEvent(event="ready", data=ready)
        async for entry in feed.entries:
            if isinstance(entry, LogStreamEnd):
                yield ServerSentEvent(
                    event="end", data=_LogEndOutput(status=entry)
                )
            else:
                if not ready_on_open:
                    yield ServerSentEvent(event="ready", data=ready)
                    ready_on_open = True
                yield ServerSentEvent(event="log", data=output(entry))
