"""Apply panel filters and paging to the payment reader."""

from papilio.schemas.results import PagedType

from ...domain.dtos.search import PaymentSearch
from ...domain.models.records import PaymentModel
from ...infra.pg.readers.search import PaymentReader


class PaymentSearchQuery:
    def __init__(self, reader: PaymentReader) -> None:
        """Bind the current payment search reader.

        Args:
            reader: PostgreSQL reader for filtered payments.

        Returns:
            None.
        """
        self.reader = reader

    async def search(self, data: PaymentSearch) -> PagedType[PaymentModel]:
        """Search payment records for the panel.

        Args:
            data: Validated search filters and paging.

        Returns:
            The page and unpaged matching total.
        """
        page = await self.reader.search(
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
            q=data.q,
            customer_id=data.customer_id,
            card_id=data.card_id,
            status=data.status,
        )
        return page
