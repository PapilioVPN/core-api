"""Prepare one cursor page for the registry's Node picker."""

from ...domain.dtos.records import NodeSelectionInput
from ...domain.results.records import NodeSelection
from ..interfaces.selection import INodeSelectionReader


class NodeSelectionQuery:
    def __init__(self, reader: INodeSelectionReader) -> None:
        self.reader = reader

    async def get(self, data: NodeSelectionInput) -> NodeSelection:
        """Read ordered choices and supply a cursor when a further row exists.

        Args:
            data: The Panel's optional search, enabled state and page bounds.

        Returns:
            One compact page correlated by registry ID.
        """
        rows = await self.reader.select_choices(
            before_id=data.before_id,
            limit=data.per_page + 1,
            q=data.q,
            is_enabled=data.is_enabled,
        )
        items = rows[: data.per_page]
        next_id = items[-1].id if len(rows) > data.per_page else None
        return NodeSelection(items, next_id)
