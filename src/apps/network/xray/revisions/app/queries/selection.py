"""Prepare one bounded page of choices for the revision picker."""

from ...domain.dtos.records import XrayRevisionSelectionInput
from ...domain.results.records import XrayRevisionSelection
from ..interfaces.records import IXrayRevisionReader


class XrayRevisionSelectionQuery:
    def __init__(self, reader: IXrayRevisionReader) -> None:
        self.reader = reader

    async def get(
        self, data: XrayRevisionSelectionInput
    ) -> XrayRevisionSelection:
        """Read a page without counting or fetching source.

        Args:
            data: Validated page size and optional exclusive ID cursor.

        Returns:
            The newest eligible choices and a cursor only if more are visible.
        """
        rows = await self.reader.select_choices(
            before_id=data.before_id, limit=data.per_page + 1
        )
        items = rows[: data.per_page]
        next_id = items[-1].id if len(rows) > data.per_page else None
        return XrayRevisionSelection(items, next_id)
