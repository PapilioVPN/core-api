"""Typed host, runtime, CPU and memory observations; sizes are bytes."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class HostInfo:
    observed_at: datetime
    hostname: str
    operating_system: str
    release: str
    version: str
    machine: str
    booted_at: datetime
    uptime_seconds: float


@dataclass(frozen=True, slots=True)
class RuntimeInfo:
    observed_at: datetime
    python_version: str
    implementation: str
    compiler: str
    executable: str
    process_id: int
    process_started_at: datetime
    process_cpu_count: int | None


@dataclass(frozen=True, slots=True)
class UserSession:
    username: str
    terminal: str | None
    host: str | None
    started_at: datetime
    process_id: int | None


@dataclass(frozen=True, slots=True)
class CpuTimes:
    user_seconds: float
    system_seconds: float
    idle_seconds: float
    nice_seconds: float | None
    iowait_seconds: float | None
    irq_seconds: float | None
    softirq_seconds: float | None
    steal_seconds: float | None
    guest_seconds: float | None
    guest_nice_seconds: float | None


@dataclass(frozen=True, slots=True)
class CpuFrequency:
    current_mhz: float
    minimum_mhz: float | None
    maximum_mhz: float | None


@dataclass(frozen=True, slots=True)
class CpuInfo:
    observed_at: datetime
    logical_count: int | None
    physical_count: int | None
    process_cpu_count: int | None
    load_average: tuple[float, float, float] | None
    frequencies: tuple[CpuFrequency, ...] | None
    times: CpuTimes
    per_cpu_times: tuple[CpuTimes, ...]
    context_switches: int
    interrupts: int
    soft_interrupts: int | None
    system_calls: int | None


@dataclass(frozen=True, slots=True)
class CpuUsage:
    observed_at: datetime
    sample_seconds: float
    percent: float


@dataclass(frozen=True, slots=True)
class CoreCpuUsage:
    observed_at: datetime
    sample_seconds: float
    percentages: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class MemoryInfo:
    observed_at: datetime
    total_bytes: int
    available_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float
    active_bytes: int | None
    inactive_bytes: int | None
    buffers_bytes: int | None
    cached_bytes: int | None
    shared_bytes: int | None
    slab_bytes: int | None


@dataclass(frozen=True, slots=True)
class SwapInfo:
    observed_at: datetime
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float
    swapped_in_bytes: int
    swapped_out_bytes: int
