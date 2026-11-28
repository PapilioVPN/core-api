"""Admit independent restarts for one saved revision and selected instances."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.network.xray.revisions.app.interfaces.records import (
    IXrayRevisionService,
)

from ...domain.dtos.fleet import XrayFleetRestartInput
from ...domain.enums.start import XrayExecutionAction
from ...domain.events.control import XrayControlRequested
from ...domain.results.fleet import XrayFleetOperationResult
from ...infra.broker.publishers import control_requested
from ..services.fleet_admission import XrayFleetAdmission


class XrayFleetRestartCommand:
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
    async def restart(
        self, revision_id: int, data: XrayFleetRestartInput
    ) -> tuple[XrayFleetOperationResult, ...]:
        """Commit the accepted restarts and their independent control events.

        Args:
            revision_id: Saved source to start after each confirmed Stop.
            data: Selected instances and their per-target request keys.

        Returns:
            Ordered admission outcomes, including replays and rejections.

        Raises:
            NotFoundException: The saved revision does not exist.
        """
        await self.revisions.lock_for_reference(revision_id)
        keys = tuple(
            (row.node_id, row.instance_id, row.request_key)
            for row in data.targets
        )
        reserved = await self.admission.reserve(
            keys, action=XrayExecutionAction.RESTART, revision_id=revision_id
        )
        await self.outbox.append_batch(
            control_requested,
            [
                XrayControlRequested(operation_id=id)
                for id in reserved.inserted_ids
            ],
        )
        return reserved.results
