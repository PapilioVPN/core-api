"""Read WireGuard diagnostic events without losing timestamp precision."""

from ...domain.results.logs import WireGuardLogEvent
from .v1 import wireguard_diagnostics_pb2 as wire


def decode(reply: wire.WireGuardLogEvent) -> WireGuardLogEvent | None:
    result = None
    if reply.sequence and reply.kind and reply.HasField("at"):
        try:
            observed_at = reply.at.ToNanoseconds()
        except ValueError:
            pass
        else:
            result = WireGuardLogEvent(
                sequence=reply.sequence,
                observed_at_unix_nanoseconds=observed_at,
                kind=reply.kind,
            )
    return result
