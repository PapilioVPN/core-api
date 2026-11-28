"""Change the operator state of a bounded registry selection."""

from papilio.infra.db.tools.decorators import transactional

from ...domain.dtos.records import NodeStateInput
from ...domain.enums.state import NodeStateStatus
from ...domain.results.records import NodeStateResult
from ..interfaces.repositories import INodeRepository


class NodeStateCommand:
    def __init__(self, repo: INodeRepository) -> None:
        self.repo = repo

    @transactional
    async def set_enabled(
        self, data: NodeStateInput
    ) -> tuple[NodeStateResult, ...]:
        """Apply the selected state and report outcomes in selection order.

        Args:
            data: Registry IDs and the intended enabled state.

        Returns:
            One result per distinct ID, including missing and unchanged rows.
        """
        ids = tuple(dict.fromkeys(data.node_ids))
        current = await self.repo.lock_enabled(ids)
        changed = tuple(
            id
            for id in ids
            if id in current and current[id] != data.is_enabled
        )
        if changed:
            await self.repo.set_enabled(changed, data.is_enabled)
        updated = set(changed)
        results = []
        for id in ids:
            if id in updated:
                status = NodeStateStatus.UPDATED
            elif id in current:
                status = NodeStateStatus.UNCHANGED
            else:
                status = NodeStateStatus.NODE_NOT_FOUND
            results.append(
                NodeStateResult(
                    id, status, data.is_enabled if id in current else None
                )
            )
        return tuple(results)
