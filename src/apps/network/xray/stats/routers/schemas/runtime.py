"""Panel schema for the live Xray runtime snapshot."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
)


class XrayRuntimeOutput(BaseOutput):
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


class XrayRuntimeObservationOutput(NodeObservationOutput):
    instance_id: str
    runtime: XrayRuntimeOutput | None
