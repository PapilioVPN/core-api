"""Admit a bounded set of Xray stops and publish only newly reserved IDs."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter

from ...domain.dtos.fleet import XrayFleetStopInput
from ...domain.enums.start import XrayExecutionAction
from ...domain.events.control import XrayControlRequested
from ...domain.results.fleet import XrayFleetOperationResult
from ...infra.broker.publishers import control_requested
from ..services.fleet_admission import XrayFleetAdmission


class XrayFleetStopCommand:
    def __init__(
        self, admission: XrayFleetAdmission, outbox: OutboxWriter
    ) -> None:
        self.admission = admission
        self.outbox = outbox

    @transactional
    async def stop(
        self, data: XrayFleetStopInput
    ) -> tuple[XrayFleetOperationResult, ...]:
        """Commit independent Stop intents and their existing control events.

        Args:
            data: Distinct instance pairs and their scoped request keys.

        Returns:
            Ordered results including replays and local rejections.
        """
        keys = tuple(
            (row.node_id, row.instance_id, row.request_key)
            for row in data.targets
        )
        reserved = await self.admission.reserve(
            keys, action=XrayExecutionAction.STOP, revision_id=None
        )
        await self.outbox.append_batch(
            control_requested,
            [
                XrayControlRequested(operation_id=id)
                for id in reserved.inserted_ids
            ],
        )
        return reserved.results
