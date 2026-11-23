"""Apply the panel's filters and paging to the payment reader."""

from papilio.schemas.results import PagedType

from ...domain.dtos.search import PaymentSearch
from ...domain.models.records import PaymentModel
from ...infra.pg.readers.search import PaymentReader


class PaymentSearchQuery:
    def __init__(self, reader: PaymentReader) -> None:
        """Bind the current request's payment reader.

        Args:
            reader: PostgreSQL payment search reader.

        Returns:
            None.
        """
        self.reader = reader

    async def search(self, data: PaymentSearch) -> PagedType[PaymentModel]:
        """Read one filtered payment page.

        Args:
            data: Validated customer, source, status and paging filters.

        Returns:
            The matching page and total before pagination.
        """
        page = await self.reader.search(
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
            customer_id=data.customer_id,
            source=data.source,
            source_id=data.source_id,
            status=data.status,
        )
        return page
