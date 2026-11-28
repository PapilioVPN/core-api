"""Panel schema for OpenVPN status evidence."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.domain.enums.observation import NodeInstanceState
from src.apps.network.nodes.routers.schemas.observation import (
    NodeObservationOutput,
)


class OpenVPNStatusOutput(BaseOutput):
    state: NodeInstanceState
    openvpn_version: str | None
    node_version: str | None
    execution_id: str | None
    applied_config_sha256: str | None


class OpenVPNStatusObservationOutput(NodeObservationOutput):
    instance_id: str
    instance: OpenVPNStatusOutput | None
