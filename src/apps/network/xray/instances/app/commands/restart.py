"""Request a forced restart with a selected immutable Xray source."""

from uuid import UUID

from papilio.infra.db.tools.decorators import transactional

from src.apps.network.xray.revisions.app.interfaces.records import (
    IXrayRevisionService,
)

from ...domain.enums.start import XrayExecutionAction
from ...domain.models.start import XrayStartModel
from ..interfaces.start import IXrayStartAdmission


class XrayRestartCommand:
    def __init__(
        self, revisions: IXrayRevisionService, admission: IXrayStartAdmission
    ) -> None:
        self.revisions = revisions
        self.admission = admission

    @transactional
    async def restart(
        self,
        node_id: int,
        instance_id: str,
        revision_id: int,
        request_key: UUID,
    ) -> XrayStartModel:
        """Register a forced restart using the operator-selected revision.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native Xray instance identity.
            revision_id: Immutable source selected for the new execution.
            request_key: Operator request identity within this target.

        Returns:
            The durable operation and its tracking identity.

        Raises:
            NotFoundException: The revision or Node is absent.
            ConflictException: The target is unavailable or the key conflicts.
        """
        await self.revisions.get_by_id(revision_id)
        operation = await self.admission.submit(
            node_id,
            instance_id,
            request_key,
            revision_id=revision_id,
            action=XrayExecutionAction.RESTART,
        )
        return operation
