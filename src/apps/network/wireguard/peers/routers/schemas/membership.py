"""Panel output for the observed WireGuard peer set."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
)


class WireGuardPeerOutput(BaseOutput):
    public_key: str
    allowed_ips: tuple[str, ...]


class WireGuardMembershipOutput(NodeObservationOutput):
    name: str
    peers: list[WireGuardPeerOutput] | None
