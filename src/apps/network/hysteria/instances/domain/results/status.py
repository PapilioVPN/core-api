"""Observed Hysteria status evidence."""

from dataclasses import dataclass

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeInstanceState,
)


@dataclass(frozen=True, slots=True)
class HysteriaStatus:
    state: NodeInstanceState
    hysteria_version: str | None
    node_version: str | None
    applied_config_sha256: str | None
