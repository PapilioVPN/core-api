"""Apply one saved revision through the shared Xray execution admission."""

from uuid import UUID

from papilio.infra.db.tools.decorators import transactional

from src.apps.network.xray.revisions.app.interfaces.records import (
    IXrayRevisionService,
)

from ...domain.models.start import XrayStartModel
from ..interfaces.start import IXrayStartAdmission


class XrayApplyCommand:
    def __init__(
        self, revisions: IXrayRevisionService, admission: IXrayStartAdmission
    ) -> None:
        self.revisions = revisions
        self.admission = admission

    @transactional
    async def apply(
        self,
        node_id: int,
        instance_id: str,
        revision_id: int,
        request_key: UUID,
    ) -> XrayStartModel:
        """Accept a saved revision for one registered instance.

        Args:
            node_id: Stable node registry identity.
            instance_id: Native Xray instance identity.
            revision_id: Immutable source revision selected by the operator.
            request_key: Operator request identity within this target.

        Returns:
            The durable operation and its tracking identity.

        Raises:
            NotFoundException: The revision or Node does not exist.
            ConflictException: The target is unavailable or the key conflicts.
        """
        await self.revisions.lock_for_reference(revision_id)
        operation = await self.admission.submit(
            node_id, instance_id, request_key, revision_id=revision_id
        )
        return operation
