"""Process-wide counters and optional uptime of the selected interface."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WireGuardRuntime:
    goroutines: int
    gc_count: int
    heap_bytes: int
    allocated_bytes: int
    system_bytes: int
    allocations: int
    frees: int
    live_objects: int
    gc_pause_nanoseconds: int
    uptime_seconds: int | None
