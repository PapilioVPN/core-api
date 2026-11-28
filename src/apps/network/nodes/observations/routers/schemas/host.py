"""Typed panel snapshot with precise unsigned counters and nulls."""

from datetime import datetime
from typing import Self

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.host import HostStatsStatus
from ...domain.results.host import HostStatsResult
from .observation import UInt64Text


class HostCPUOutput(BaseOutput):
    busy_percent: float
    steal_percent: float | None
    window_milliseconds: UInt64Text
    observed_at: datetime | None


class HostMemoryOutput(BaseOutput):
    total_bytes: UInt64Text
    available_bytes: UInt64Text | None
    used_bytes: UInt64Text | None
    swap_total_bytes: UInt64Text
    swap_free_bytes: UInt64Text


class HostStorageOutput(BaseOutput):
    path: str
    total_bytes: UInt64Text
    used_bytes: UInt64Text
    available_bytes: UInt64Text
    read_only: bool


class HostNetworkOutput(BaseOutput):
    rx_bytes_per_second: UInt64Text
    tx_bytes_per_second: UInt64Text
    window_milliseconds: UInt64Text
    observed_at: datetime | None


class HostStatsOutput(BaseOutput):
    uptime_seconds: UInt64Text | None
    logical_cpu_count: int | None
    cpu: HostCPUOutput | None
    memory: HostMemoryOutput | None
    storage: HostStorageOutput | None
    network: HostNetworkOutput | None


class NodeHostOutput(BaseOutput):
    node_id: int
    status: HostStatsStatus
    stats: HostStatsOutput | None
    received_at: datetime | None

    @classmethod
    def from_result(cls, id: int, result: HostStatsResult) -> Self:
        """Expose the snapshot and observation status in either view."""
        return cls(
            node_id=id,
            status=result.status,
            stats=HostStatsOutput.from_obj(result.stats)
            if result.stats
            else None,
            received_at=result.received_at,
        )
