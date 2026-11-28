"""Typed Hysteria dry run boundary."""

from typing import Protocol

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.dtos.dry_run import HysteriaCandidate
from ...domain.results.dry_run import HysteriaValidation


class IHysteriaValidationGateway(Protocol):
    async def validate(
        self, node: NodeModel, instance_id: str, source: bytes
    ) -> NodeObservation[HysteriaValidation]: ...


class IHysteriaValidationService(Protocol):
    async def validate(
        self, node_id: int, instance_id: str, data: HysteriaCandidate
    ) -> NodeObservation[HysteriaValidation]: ...
