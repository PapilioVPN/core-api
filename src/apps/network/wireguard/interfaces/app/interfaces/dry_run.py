"""Typed WireGuard dry run boundary."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.dtos.dry_run import WireGuardCandidate
from ...domain.results.dry_run import WireGuardValidation


class IWireGuardValidationGateway(Protocol):
    async def validate(
        self, node: NodeModel, target_name: str, source: bytes
    ) -> NodeObservation[WireGuardValidation]: ...


class IWireGuardValidationService(Protocol):
    async def validate(
        self, node_id: int, target_name: str, data: WireGuardCandidate
    ) -> NodeObservation[WireGuardValidation]: ...
