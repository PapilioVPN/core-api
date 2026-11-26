"""Validate exact candidate bytes without changing the running engine."""

from hashlib import sha256

from src.apps.network.nodes.app.interfaces.services import INodeService

from ...domain.dtos.validation import XrayConfigCandidate
from ...domain.enums.validation import XrayValidationStatus
from ...domain.results.validation import (
    XrayConfigValidation,
    XrayValidationOutcome,
)
from ..interfaces.validation import IXrayConfigGateway


class XrayConfigValidationService:
    def __init__(
        self, nodes: INodeService, gateway: IXrayConfigGateway
    ) -> None:
        """Bind the registry and the Xray-native validation gateway."""
        self.nodes = nodes
        self.gateway = gateway

    async def validate(
        self,
        node_id: int,
        instance_id: str,
        candidate: XrayConfigCandidate,
    ) -> XrayConfigValidation:
        """Dry-run one candidate on the enabled Node selected by the Panel.

        Args:
            node_id: Stable identity from the registry.
            instance_id: Native Xray instance ID on that node.
            candidate: Validated input holding the exact proposed UTF-8 bytes.

        Returns:
            A typed outcome and the SHA-256 of the proposed bytes.

        Raises:
            NotFoundException: The node ID is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        source = candidate.config_json
        if node.is_enabled:
            outcome = await self.gateway.validate(
                node_id=node_id,
                address=node.address,
                port=node.port,
                instance_id=instance_id,
                source=source,
            )
        else:
            outcome = XrayValidationOutcome(XrayValidationStatus.DISABLED)
        return XrayConfigValidation(
            node_id,
            instance_id,
            sha256(source).hexdigest(),
            outcome.status,
            outcome.issue,
        )
