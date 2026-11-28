"""Decode the named interface observation and its optional digest."""

from src.apps.network.nodes.infra.grpc.observation import valid_config_digest

from ...domain.results.status import WireGuardStatus
from .v1.interfaces_pb2 import WireGuardInterfaceStatus


def decode(
    reply: WireGuardInterfaceStatus, name: str
) -> WireGuardStatus | None:
    """Require the selected interface and its positive MTU in bytes."""
    digest = (
        reply.applied_config_sha256
        if reply.HasField("applied_config_sha256")
        else None
    )
    result = None
    if (
        reply.name == name
        and reply.mtu > 0
        and (digest is None or valid_config_digest(digest))
    ):
        result = WireGuardStatus(
            up=reply.up,
            mtu=reply.mtu,
            interface_index=reply.interface_index or None,
            node_version=reply.node_version or None,
            kernel_release=reply.kernel_release or None,
            wireguard_tools_version=reply.wireguard_tools_version or None,
            applied_config_sha256=digest,
        )
    return result
