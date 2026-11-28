"""Panel schema for WireGuard status evidence."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    NodeObservationOutput,
)


class WireGuardStatusOutput(BaseOutput):
    up: bool
    mtu: int
    interface_index: int | None
    node_version: str | None
    kernel_release: str | None
    wireguard_tools_version: str | None
    applied_config_sha256: str | None


class WireGuardStatusObservationOutput(NodeObservationOutput):
    name: str
    interface: WireGuardStatusOutput | None
