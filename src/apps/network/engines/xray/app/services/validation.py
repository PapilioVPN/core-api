"""Validate exact candidate bytes without changing the running engine."""

from hashlib import sha256

from src.apps.network.nodes.app.interfaces.services import INodeService

from ...domain.dtos.validation import XrayConfigCandidate
from ...domain.enums.validation import XrayValidationStatus
from ...domain.results.validation import (
    XrayConfigValidation,
    XrayValidationOutcome,
)
from ..interfaces.revisions import IXrayRevisionService
from ..interfaces.validation import IXrayConfigGateway


class XrayConfigValidationService:
    def __init__(
        self,
        nodes: INodeService,
        gateway: IXrayConfigGateway,
        revisions: IXrayRevisionService,
    ) -> None:
        """Bind the registry and the Xray-native validation gateway."""
        self.nodes = nodes
        self.gateway = gateway
        self.revisions = revisions

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
        source = candidate.config_json
        result = await self._validate(
            node_id, instance_id, source, sha256(source).hexdigest()
        )
        return result

    async def validate_revision(
        self, node_id: int, instance_id: str, revision_id: int
    ) -> XrayConfigValidation:
        """Dry-run the exact stored revision, without a caller-supplied body.

        Args:
            node_id: Stable registered node identity.
            instance_id: Native Xray instance ID on that node.
            revision_id: Stable immutable revision identity.

        Returns:
            The outcome for the stored digest on the selected instance.

        Raises:
            NotFoundException: The node or revision is absent.
            XrayRevisionSourceUnavailable: The source cannot be recovered.
        """
        revision = await self.revisions.get_source(revision_id)
        result = await self._validate(
            node_id, instance_id, revision.config_json, revision.config_sha256
        )
        return result

    async def _validate(
        self, node_id: int, instance_id: str, source: bytes, digest: str
    ) -> XrayConfigValidation:
        node = await self.nodes.get_by_id(node_id)
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
            digest,
            outcome.status,
            outcome.issue,
        )
