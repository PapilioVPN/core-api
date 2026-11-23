"""Filesystem and device observations; I/O counters are cumulative."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DiskPartition:
    device: str
    mountpoint: str
    filesystem: str
    read_only: bool


@dataclass(frozen=True, slots=True)
class DiskUsage:
    observed_at: datetime
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


@dataclass(frozen=True, slots=True)
class DiskIoCounters:
    observed_at: datetime
    device: str | None
    read_count: int
    write_count: int
    read_bytes: int
    write_bytes: int
    read_time_ms: int
    write_time_ms: int
    read_merged_count: int | None
    write_merged_count: int | None
    busy_time_ms: int | None
