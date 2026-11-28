"""Compare assigned source bytes with a fresh, on-demand Node observation."""

from src.apps.network.xray.instances.app.interfaces.status import (
    IXrayStatusQuery,
)

from ...domain.results.records import XrayRevisionComparison
from ..interfaces.records import IXrayAssignmentQuery
from ..policies.comparison import build_comparison


class XrayRevisionComparisonQuery:
    def __init__(
        self, assignments: IXrayAssignmentQuery, status: IXrayStatusQuery
    ) -> None:
        self.assignments = assignments
        self.status = status

    async def get(
        self, node_id: int, instance_id: str
    ) -> XrayRevisionComparison:
        """Skip the remote read when there is nothing to compare."""
        selected = await self.assignments.get(node_id, instance_id)
        observed = (
            await self.status.observe_target(selected.endpoint, instance_id)
            if selected.desired is not None
            else None
        )
        return build_comparison(selected.desired, observed)
