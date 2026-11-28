"""Panel output for one WireGuard egress observation."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
    UInt64Text,
)


class WireGuardEgressOutput(BaseOutput):
    reachable: bool
    http_status: int | None
    elapsed_nanoseconds: UInt64Text
    observed_at_unix_nanoseconds: UInt64Text


class WireGuardEgressObservationOutput(NodeObservationOutput):
    name: str
    egress: WireGuardEgressOutput | None
