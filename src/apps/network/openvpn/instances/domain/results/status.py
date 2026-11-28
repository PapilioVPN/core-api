"""Observed OpenVPN status evidence."""

from dataclasses import dataclass

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeInstanceState,
)


@dataclass(frozen=True, slots=True)
class OpenVPNStatus:
    state: NodeInstanceState
    openvpn_version: str | None
    node_version: str | None
    execution_id: str | None
    applied_config_sha256: str | None
