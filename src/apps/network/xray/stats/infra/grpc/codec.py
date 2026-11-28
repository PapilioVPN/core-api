"""Map the native runtime metrics to a typed observation."""

from ...domain.results.runtime import XrayRuntime
from ...domain.results.traffic import XrayTraffic
from .v1.runtime_stats_pb2 import XrayRuntimeStats
from .v1.traffic_pb2 import XrayTrafficList, XrayTrafficUsage


def decode_runtime(reply: XrayRuntimeStats) -> XrayRuntime:
    """Preserve Node's integer metric values and units."""
    return XrayRuntime(
        goroutines=reply.goroutines,
        gc_count=reply.gc_count,
        heap_allocated_bytes=reply.heap_allocated_bytes,
        total_allocated_bytes=reply.total_allocated_bytes,
        system_bytes=reply.system_bytes,
        mallocs=reply.mallocs,
        frees=reply.frees,
        live_objects=reply.live_objects,
        gc_pause_total_nanoseconds=reply.gc_pause_total_nanoseconds,
        uptime_seconds=reply.uptime_seconds,
    )


def _entry(reply: XrayTrafficUsage) -> XrayTraffic | None:
    uplink = reply.uplink_bytes if reply.HasField("uplink_bytes") else None
    downlink = (
        reply.downlink_bytes if reply.HasField("downlink_bytes") else None
    )
    return (
        XrayTraffic(reply.name, uplink, downlink)
        if reply.name and (uplink is not None or downlink is not None)
        else None
    )


def decode_counter(reply: XrayTrafficUsage, name: str) -> XrayTraffic | None:
    """Correlate the exact name and preserve counter presence."""
    return _entry(reply) if reply.name == name else None


def decode_traffic(reply: XrayTrafficList) -> tuple[XrayTraffic, ...] | None:
    """Retain observed empty snapshots and reject malformed rows."""
    entries: list[XrayTraffic] = []
    valid = True
    for reply_row in reply.entries:
        entry = _entry(reply_row)
        if entry is None:
            valid = False
            break
        entries.append(entry)
    return tuple(entries) if valid else None
