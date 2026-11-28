"""Decode a correlated Node Hysteria lifecycle observation."""

from src.apps.network.nodes.domain.enums.observation import NodeInstanceState
from src.apps.network.nodes.infra.grpc.observation import valid_config_digest

from ...domain.results.status import HysteriaStatus
from .v1.hysteria_instances_pb2 import HysteriaInstanceState as WireState
from .v1.hysteria_instances_pb2 import HysteriaInstanceStatus

_STATES = {
    WireState.HYSTERIA_INSTANCE_STATE_STOPPED: NodeInstanceState.STOPPED,
    WireState.HYSTERIA_INSTANCE_STATE_STARTING: NodeInstanceState.STARTING,
    WireState.HYSTERIA_INSTANCE_STATE_READY: NodeInstanceState.READY,
    WireState.HYSTERIA_INSTANCE_STATE_STOPPING: NodeInstanceState.STOPPING,
    WireState.HYSTERIA_INSTANCE_STATE_FAILED: NodeInstanceState.FAILED,
}


def decode(
    reply: HysteriaInstanceStatus, instance_id: str
) -> HysteriaStatus | None:
    """Require a matching ID and a digest consistent with readiness."""
    state = _STATES.get(reply.state)
    digest = (
        reply.applied_config_sha256
        if reply.HasField("applied_config_sha256")
        else None
    )
    result = None
    if (
        reply.id == instance_id
        and state is not None
        and (
            digest is None
            or (
                state is NodeInstanceState.READY
                and valid_config_digest(digest)
            )
        )
    ):
        result = HysteriaStatus(
            state=state,
            hysteria_version=reply.hysteria_version or None,
            node_version=reply.node_version or None,
            applied_config_sha256=digest,
        )
    return result
