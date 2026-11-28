"""Admit a saved revision for a bounded selection of independent instances."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.network.xray.revisions.app.interfaces.records import (
    IXrayRevisionService,
)

from ...domain.dtos.fleet_apply import XrayFleetApplyInput
from ...domain.enums.start import XrayExecutionAction
from ...domain.events.apply import XrayApplyRequested
from ...domain.results.fleet import XrayFleetOperationResult
from ...infra.broker.publishers import apply_requested
from ..services.fleet_admission import XrayFleetAdmission


class XrayFleetApplyCommand:
    def __init__(
        self,
        revisions: IXrayRevisionService,
        admission: XrayFleetAdmission,
        outbox: OutboxWriter,
    ) -> None:
        self.revisions = revisions
        self.admission = admission
        self.outbox = outbox

    @transactional
    async def apply(
        self,
        revision_id: int,
        data: XrayFleetApplyInput,
    ) -> tuple[XrayFleetOperationResult, ...]:
        """Commit accepted operations and identity-only events together."""
        await self.revisions.lock_for_reference(revision_id)
        keys = tuple(
            (row.node_id, row.instance_id, row.request_key)
            for row in data.targets
        )
        reserved = await self.admission.reserve(
            keys, action=XrayExecutionAction.START, revision_id=revision_id
        )
        await self.outbox.append_batch(
            apply_requested,
            [
                XrayApplyRequested(operation_id=id)
                for id in reserved.inserted_ids
            ],
        )
        return reserved.results
