"""Decode Xray v1 instance observations."""

from re import fullmatch

from ...domain.enums.status import XrayInstanceState
from ...domain.results.status import XrayInstanceObservation
from .v1.instances_pb2 import XrayInstanceState as WireState
from .v1.instances_pb2 import XrayInstanceStatus

_STATES = {
    WireState.XRAY_INSTANCE_STATE_STOPPED: XrayInstanceState.STOPPED,
    WireState.XRAY_INSTANCE_STATE_STARTING: XrayInstanceState.STARTING,
    WireState.XRAY_INSTANCE_STATE_READY: XrayInstanceState.READY,
    WireState.XRAY_INSTANCE_STATE_STOPPING: XrayInstanceState.STOPPING,
    WireState.XRAY_INSTANCE_STATE_FAILED: XrayInstanceState.FAILED,
}


def decode_instance(
    reply: XrayInstanceStatus, instance_id: str
) -> XrayInstanceObservation | None:
    """Accept only correlated state and evidence consistent with Node v1."""
    state = _STATES.get(reply.state)
    digest = (
        reply.applied_config_sha256
        if reply.HasField("applied_config_sha256")
        else None
    )
    observation = None
    if (
        reply.id == instance_id
        and state is not None
        and (
            digest is None
            or (
                state is XrayInstanceState.READY
                and fullmatch(r"[a-f0-9]{64}", digest) is not None
            )
        )
    ):
        observation = XrayInstanceObservation(
            state=state,
            xray_version=reply.xray_version or None,
            node_version=reply.node_version or None,
            applied_config_sha256=digest,
        )
    return observation
