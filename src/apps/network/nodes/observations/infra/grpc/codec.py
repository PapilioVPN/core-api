"""Map the versioned host reply without filling absent metrics with zeros."""

from datetime import UTC

from ...domain.results.host import (
    HostCPU,
    HostMemory,
    HostNetwork,
    HostStats,
    HostStorage,
)
from .v1.host_pb2 import (
    CPUSnapshot,
    MemorySnapshot,
    NetworkSnapshot,
    StorageSnapshot,
    SystemSnapshot,
)


def _cpu(value: CPUSnapshot) -> HostCPU:
    return HostCPU(
        busy_percent=value.busy_percent,
        steal_percent=value.steal_percent
        if value.HasField("steal_percent")
        else None,
        window_milliseconds=value.window_milliseconds,
        observed_at=value.observed_at.ToDatetime(UTC)
        if value.HasField("observed_at")
        else None,
    )


def _memory(value: MemorySnapshot) -> HostMemory:
    return HostMemory(
        total_bytes=value.total_bytes,
        available_bytes=value.available_bytes
        if value.HasField("available_bytes")
        else None,
        used_bytes=value.used_bytes if value.HasField("used_bytes") else None,
        swap_total_bytes=value.swap_total_bytes,
        swap_free_bytes=value.swap_free_bytes,
    )


def _storage(value: StorageSnapshot) -> HostStorage:
    return HostStorage(
        path=value.path,
        total_bytes=value.total_bytes,
        used_bytes=value.used_bytes,
        available_bytes=value.available_bytes,
        read_only=value.read_only,
    )


def _network(value: NetworkSnapshot) -> HostNetwork:
    return HostNetwork(
        rx_bytes_per_second=value.rx_bytes_per_second,
        tx_bytes_per_second=value.tx_bytes_per_second,
        window_milliseconds=value.window_milliseconds,
        observed_at=value.observed_at.ToDatetime(UTC)
        if value.HasField("observed_at")
        else None,
    )


def decode_host(value: SystemSnapshot) -> HostStats:
    """Preserve Node's field presence, integer values and sampling units."""
    return HostStats(
        uptime_seconds=value.uptime_seconds
        if value.HasField("uptime_seconds")
        else None,
        # The Node sampler's zero count means it could not read /proc/stat.
        logical_cpu_count=value.logical_cpu_count or None,
        cpu=_cpu(value.cpu) if value.HasField("cpu") else None,
        memory=_memory(value.memory) if value.HasField("memory") else None,
        storage=_storage(value.storage) if value.HasField("storage") else None,
        network=_network(value.network) if value.HasField("network") else None,
    )
