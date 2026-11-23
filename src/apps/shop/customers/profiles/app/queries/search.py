"""Apply panel search inputs to current customer records."""

from papilio.schemas.results import PagedType

from ...domain.dtos.search import ProfileSearch
from ...domain.models.records import CustomerModel
from ...infra.pg.readers.search import ProfileReader


class ProfileSearchQuery:
    def __init__(self, reader: ProfileReader) -> None:
        """Bind panel search to the current request.

        Args:
            reader: PostgreSQL customer search reader.

        Returns:
            None.
        """
        self.reader = reader

    async def search(self, data: ProfileSearch) -> PagedType[CustomerModel]:
        """Read a filtered page from current customer state.

        Args:
            data: Validated text, group, block state and paging inputs.

        Returns:
            The page and matching total.
        """
        page = await self.reader.search(
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
            q=data.q,
            group_id=data.group_id,
            is_blocked=data.is_blocked,
        )
        return page
