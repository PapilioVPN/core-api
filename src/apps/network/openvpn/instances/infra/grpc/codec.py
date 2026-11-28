"""Decode a correlated Node OpenVPN lifecycle observation."""

from src.apps.network.nodes.connections.infra.grpc.observation import (
    valid_config_digest,
)
from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeInstanceState,
)

from ...domain.results.status import OpenVPNStatus
from .v1.openvpn_instances_pb2 import OpenVPNInstanceState as WireState
from .v1.openvpn_instances_pb2 import OpenVPNInstanceStatus

_STATES = {
    WireState.OPEN_VPN_INSTANCE_STATE_STOPPED: NodeInstanceState.STOPPED,
    WireState.OPEN_VPN_INSTANCE_STATE_STARTING: NodeInstanceState.STARTING,
    WireState.OPEN_VPN_INSTANCE_STATE_READY: NodeInstanceState.READY,
    WireState.OPEN_VPN_INSTANCE_STATE_STOPPING: NodeInstanceState.STOPPING,
    WireState.OPEN_VPN_INSTANCE_STATE_FAILED: NodeInstanceState.FAILED,
}


def decode(
    reply: OpenVPNInstanceStatus, instance_id: str
) -> OpenVPNStatus | None:
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
        result = OpenVPNStatus(
            state=state,
            openvpn_version=reply.openvpn_version or None,
            node_version=reply.node_version or None,
            execution_id=reply.execution_id or None,
            applied_config_sha256=digest,
        )
    return result
