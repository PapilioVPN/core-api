"""Filesystem and device observations; I/O counters are cumulative."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class PartitionOutput(BaseOutput):
    device: str
    mountpoint: str
    filesystem: str
    read_only: bool


class DiskUsageOutput(BaseOutput):
    observed_at: datetime
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


class DiskIoOutput(BaseOutput):
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
