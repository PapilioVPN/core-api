"""Queue local-source Xray Starts for an explicit fleet selection."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter

from ...domain.dtos.fleet import XrayFleetStartInput
from ...domain.enums.start import XrayExecutionAction
from ...domain.events.start import XrayStartRequested
from ...domain.results.fleet import XrayFleetOperationResult
from ...infra.broker.publishers import start_requested
from ..services.fleet_admission import XrayFleetAdmission


class XrayFleetStartCommand:
    def __init__(
        self, admission: XrayFleetAdmission, outbox: OutboxWriter
    ) -> None:
        self.admission = admission
        self.outbox = outbox

    @transactional
    async def start(
        self, data: XrayFleetStartInput
    ) -> tuple[XrayFleetOperationResult, ...]:
        """Commit local Starts and their existing events with one transaction.

        Args:
            data: Distinct instance pairs and their scoped request keys.

        Returns:
            Ordered admission results with new and replayed operation IDs.
        """
        keys = tuple(
            (row.node_id, row.instance_id, row.request_key)
            for row in data.targets
        )
        reserved = await self.admission.reserve(
            keys, action=XrayExecutionAction.START, revision_id=None
        )
        await self.outbox.append_batch(
            start_requested,
            [
                XrayStartRequested(operation_id=id)
                for id in reserved.inserted_ids
            ],
        )
        return reserved.results
