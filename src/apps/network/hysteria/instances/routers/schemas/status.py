"""Panel schema for Hysteria status evidence."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.domain.enums.observation import NodeInstanceState
from src.apps.network.nodes.routers.schemas.observation import (
    NodeObservationOutput,
)


class HysteriaStatusOutput(BaseOutput):
    state: NodeInstanceState
    hysteria_version: str | None
    node_version: str | None
    applied_config_sha256: str | None


class HysteriaStatusObservationOutput(NodeObservationOutput):
    instance_id: str
    instance: HysteriaStatusOutput | None
