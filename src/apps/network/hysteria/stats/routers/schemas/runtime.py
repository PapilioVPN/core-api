"""Panel output for the live HysteriaRuntime observation."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
    UInt64Text,
)


class HysteriaRuntimeOutput(BaseOutput):
    execution: UInt64Text
    ready_since_unix_nanoseconds: UInt64Text
    uptime_seconds: UInt64Text


class HysteriaRuntimeObservationOutput(NodeObservationOutput):
    instance_id: str
    runtime: HysteriaRuntimeOutput | None
