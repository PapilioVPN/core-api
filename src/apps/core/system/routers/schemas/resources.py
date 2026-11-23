"""Typed host, runtime, CPU and memory observations; sizes are bytes."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class HostOutput(BaseOutput):
    observed_at: datetime
    hostname: str
    operating_system: str
    release: str
    version: str
    machine: str
    booted_at: datetime
    uptime_seconds: float


class RuntimeOutput(BaseOutput):
    observed_at: datetime
    python_version: str
    implementation: str
    compiler: str
    executable: str
    process_id: int
    process_started_at: datetime
    process_cpu_count: int | None


class UserSessionOutput(BaseOutput):
    username: str
    terminal: str | None
    host: str | None
    started_at: datetime
    process_id: int | None


class CpuTimesOutput(BaseOutput):
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


class CpuFrequencyOutput(BaseOutput):
    current_mhz: float
    minimum_mhz: float | None
    maximum_mhz: float | None


class CpuOutput(BaseOutput):
    observed_at: datetime
    logical_count: int | None
    physical_count: int | None
    process_cpu_count: int | None
    load_average: tuple[float, float, float] | None
    frequencies: tuple[CpuFrequencyOutput, ...] | None
    times: CpuTimesOutput
    per_cpu_times: tuple[CpuTimesOutput, ...]
    context_switches: int
    interrupts: int
    soft_interrupts: int | None
    system_calls: int | None


class CpuUsageOutput(BaseOutput):
    observed_at: datetime
    sample_seconds: float
    percent: float


class CoreCpuUsageOutput(BaseOutput):
    observed_at: datetime
    sample_seconds: float
    percentages: tuple[float, ...]


class MemoryOutput(BaseOutput):
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


class SwapOutput(BaseOutput):
    observed_at: datetime
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float
    swapped_in_bytes: int
    swapped_out_bytes: int
