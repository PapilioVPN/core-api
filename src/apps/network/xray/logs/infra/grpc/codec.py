"""Decode the Node log wire format and observable sequence gaps."""

from ...domain.enums.live import XrayLogSource
from ...domain.results.live import XrayLogLine
from .v1 import logs_pb2 as wire

_SOURCE = {
    wire.XRAY_LOG_SOURCE_STDOUT: XrayLogSource.STDOUT,
    wire.XRAY_LOG_SOURCE_STDERR: XrayLogSource.STDERR,
}


def decode_line(
    event: wire.XrayLogEvent, previous_sequence: int | None
) -> XrayLogLine:
    """Expose text and mark losses that can be inferred from the wire."""
    encoding_replaced = False
    try:
        message = event.message.decode()
    except UnicodeDecodeError:
        message = event.message.decode(errors="replace")
        encoding_replaced = True
    return XrayLogLine(
        execution=event.execution,
        sequence=event.sequence,
        received_unix_nano=event.received_unix_nano,
        source=_SOURCE.get(event.source, XrayLogSource.UNSPECIFIED),
        message=message,
        truncated=event.truncated,
        encoding_replaced=encoding_replaced,
        missed_before=max(0, event.sequence - previous_sequence - 1)
        if previous_sequence is not None
        else None,
    )
