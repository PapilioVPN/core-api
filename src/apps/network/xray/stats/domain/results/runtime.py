"""Xray's live runtime counters and gauges in Node contract units."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class XrayRuntime:
    goroutines: int
    gc_count: int
    heap_allocated_bytes: int
    total_allocated_bytes: int
    system_bytes: int
    mallocs: int
    frees: int
    live_objects: int
    gc_pause_total_nanoseconds: int
    uptime_seconds: int
