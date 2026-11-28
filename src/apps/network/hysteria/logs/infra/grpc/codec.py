"""Decode the fixed event names carried by the Hysteria log wire format."""

from ...domain.results.logs import HysteriaLogEvent
from .v1 import hysteria_logs_pb2 as wire


def decode(reply: wire.HysteriaLogEvent) -> HysteriaLogEvent | None:
    result = None
    if (
        reply.execution
        and reply.sequence
        and reply.received_unix_nano > 0
        and reply.event
    ):
        result = HysteriaLogEvent(
            execution=reply.execution,
            sequence=reply.sequence,
            received_unix_nano=reply.received_unix_nano,
            event=reply.event,
        )
    return result
