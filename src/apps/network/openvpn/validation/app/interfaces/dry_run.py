"""Typed OpenVPN dry run boundary."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.dtos.dry_run import OpenVPNCandidate
from ...domain.results.dry_run import OpenVPNValidation


class IOpenVPNValidationGateway(Protocol):
    async def validate(
        self, node: NodeModel, instance_id: str, source: bytes
    ) -> NodeObservation[OpenVPNValidation]: ...


class IOpenVPNValidationService(Protocol):
    async def validate(
        self, node_id: int, instance_id: str, data: OpenVPNCandidate
    ) -> NodeObservation[OpenVPNValidation]: ...
