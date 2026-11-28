"""Read selected lifecycle operations without touching Node or the broker."""

from papilio.utils.dates import utc_now

from ...domain.dtos.fleet import XrayFleetTrackingInput
from ...domain.dtos.fleet_apply import XrayFleetApplyTrackingInput
from ...domain.dtos.identity import XrayExecutionTrackingKey
from ...domain.enums.fleet import XrayFleetOperationStatus
from ...domain.enums.start import XrayExecutionAction
from ...domain.models.start import XrayStartModel
from ...domain.results.fleet import XrayFleetOperationResult
from ..interfaces.start import IXrayStartRepository


def _observe(
    keys: tuple[XrayExecutionTrackingKey, ...],
    records: tuple[XrayStartModel, ...],
) -> tuple[XrayFleetOperationResult, ...]:
    indexed = {(row.node_id, row.instance_id, row.id): row for row in records}
    now = utc_now()
    results = []
    for key in keys:
        node_id, instance_id, operation_id = key
        row = indexed.get(key)
        results.append(
            XrayFleetOperationResult(
                node_id,
                instance_id,
                XrayFleetOperationStatus.ACCEPTED
                if row is not None
                else XrayFleetOperationStatus.OPERATION_NOT_FOUND,
                row.observed_at(now) if row is not None else None,
                operation_id,
            )
        )
    return tuple(results)


class XrayFleetApplyQuery:
    def __init__(self, repo: IXrayStartRepository) -> None:
        self.repo = repo

    async def get(
        self,
        revision_id: int,
        data: XrayFleetApplyTrackingInput,
    ) -> tuple[XrayFleetOperationResult, ...]:
        """Correlate durable records under the exact revision scope."""
        keys = tuple(
            (row.node_id, row.instance_id, row.operation_id)
            for row in data.targets
        )
        records = await self.repo.find_operations(
            tuple(dict.fromkeys(keys)),
            action=XrayExecutionAction.START,
            revision_id=revision_id,
        )
        return _observe(keys, records)


class XrayFleetStartQuery:
    def __init__(self, repo: IXrayStartRepository) -> None:
        self.repo = repo

    async def get(
        self, data: XrayFleetTrackingInput
    ) -> tuple[XrayFleetOperationResult, ...]:
        """Read local-source Start evidence for the selected targets.

        Args:
            data: Node, instance and operation ID tuples in requested order.

        Returns:
            One result per row. IDs for saved revision Apply are absent.
        """
        keys = tuple(
            (row.node_id, row.instance_id, row.operation_id)
            for row in data.targets
        )
        records = await self.repo.find_operations(
            tuple(dict.fromkeys(keys)),
            action=XrayExecutionAction.START,
            revision_id=None,
        )
        return _observe(keys, records)


class XrayFleetStopQuery:
    def __init__(self, repo: IXrayStartRepository) -> None:
        self.repo = repo

    async def get(
        self, data: XrayFleetTrackingInput
    ) -> tuple[XrayFleetOperationResult, ...]:
        """Read correlated Stop evidence for the bounded selection.

        Args:
            data: Node, instance and Stop operation IDs in requested order.

        Returns:
            One result per row, including missing operations and duplicates.
        """
        keys = tuple(
            (row.node_id, row.instance_id, row.operation_id)
            for row in data.targets
        )
        records = await self.repo.find_operations(
            tuple(dict.fromkeys(keys)),
            action=XrayExecutionAction.STOP,
            revision_id=None,
        )
        return _observe(keys, records)


class XrayFleetRestartQuery:
    def __init__(self, repo: IXrayStartRepository) -> None:
        self.repo = repo

    async def get(
        self, revision_id: int, data: XrayFleetTrackingInput
    ) -> tuple[XrayFleetOperationResult, ...]:
        """Read the tracked restarts for one revision in a set query.

        Args:
            revision_id: Exact saved source scope for the selected restarts.
            data: Node, instance and operation IDs in the requested order.

        Returns:
            Per-target outcomes, retaining missing results and duplicates.
        """
        keys = tuple(
            (row.node_id, row.instance_id, row.operation_id)
            for row in data.targets
        )
        records = await self.repo.find_operations(
            tuple(dict.fromkeys(keys)),
            action=XrayExecutionAction.RESTART,
            revision_id=revision_id,
        )
        return _observe(keys, records)
