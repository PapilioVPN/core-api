"""WireGuard log event bodies sent to the Panel."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    UInt64Text,
)


class WireGuardLogReadyOutput(BaseOutput):
    node_id: int
    name: str


class WireGuardLogEventOutput(BaseOutput):
    sequence: UInt64Text
    observed_at_unix_nanoseconds: UInt64Text
    kind: str
