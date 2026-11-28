"""Panel output for the live WireGuardRuntime observation."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
    UInt64Text,
)


class WireGuardRuntimeOutput(BaseOutput):
    goroutines: UInt64Text
    gc_count: int
    heap_bytes: UInt64Text
    allocated_bytes: UInt64Text
    system_bytes: UInt64Text
    allocations: UInt64Text
    frees: UInt64Text
    live_objects: UInt64Text
    gc_pause_nanoseconds: UInt64Text
    uptime_seconds: UInt64Text | None


class WireGuardRuntimeObservationOutput(NodeObservationOutput):
    name: str
    runtime: WireGuardRuntimeOutput | None
