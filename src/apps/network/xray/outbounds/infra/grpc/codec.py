"""Decode typed Observatory samples and retain missing native values."""

from ...domain.enums.health import XrayOutboundState
from ...domain.results.health import XrayOutboundSample
from .v1.outbounds_pb2 import XrayOutboundHealth, XrayOutboundObservation
from .v1.outbounds_pb2 import XrayOutboundHealthStatus as WireState

_STATES = {
    WireState.XRAY_OUTBOUND_HEALTH_STATUS_HEALTHY: XrayOutboundState.HEALTHY,
    WireState.XRAY_OUTBOUND_HEALTH_STATUS_FAILED: XrayOutboundState.FAILED,
    WireState.XRAY_OUTBOUND_HEALTH_STATUS_NO_SAMPLE: (
        XrayOutboundState.NO_SAMPLE
    ),
}


def _sample(reply: XrayOutboundObservation) -> XrayOutboundSample | None:
    state = _STATES.get(reply.status)
    result = None
    if state is not None and reply.tag:
        result = XrayOutboundSample(
            tag=reply.tag,
            status=state,
            delay_milliseconds=(
                reply.delay_milliseconds
                if reply.HasField("delay_milliseconds")
                else None
            ),
            last_seen_unix_seconds=(
                reply.last_seen_unix_seconds
                if reply.HasField("last_seen_unix_seconds")
                else None
            ),
            last_try_unix_seconds=(
                reply.last_try_unix_seconds
                if reply.HasField("last_try_unix_seconds")
                else None
            ),
        )
    return result


def decode_health(
    reply: XrayOutboundHealth, tag: str | None
) -> tuple[XrayOutboundSample, ...] | None:
    """Preserve empty snapshots and require an exact correlated tag result."""
    samples: list[XrayOutboundSample] = []
    valid = tag is None or (
        len(reply.observations) == 1 and reply.observations[0].tag == tag
    )
    if valid:
        for row in reply.observations:
            sample = _sample(row)
            if sample is None:
                valid = False
                break
            samples.append(sample)
    return tuple(samples) if valid else None
