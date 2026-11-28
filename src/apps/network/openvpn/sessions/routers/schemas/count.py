"""Panel output for the live OpenVPNSessionCount observation."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
    UInt64Text,
)


class OpenVPNSessionCountOutput(BaseOutput):
    execution_id: str
    observed_at_unix_seconds: UInt64Text
    session_count: int


class OpenVPNSessionCountObservationOutput(NodeObservationOutput):
    instance_id: str
    sessions: OpenVPNSessionCountOutput | None
