"""Typed panel snapshot with precise unsigned counters and nulls."""

from datetime import datetime
from typing import Annotated

from papilio.schemas.outputs import BaseOutput
from pydantic import Field

from ...domain.enums.host import HostStatsStatus

# Preserve uint64 precision in JavaScript, including values above 2**53.
type UInt64Text = Annotated[str, Field(coerce_numbers_to_str=True)]


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
