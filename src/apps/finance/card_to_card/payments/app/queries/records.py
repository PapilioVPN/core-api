"""Read a page of card payments using the panel's filters."""

from papilio.schemas.results import PagedType
from papilio.types.constants import INT64_MAX
from papilio.utils.dates import utc_now

from ...domain.dtos.records import CardPaymentList
from ...domain.models.records import CardPaymentModel
from ...infra.pg.repositories.crud import CardPaymentRepository


class CardPaymentQuery:
    def __init__(self, repo: CardPaymentRepository) -> None:
        self.repo = repo

    async def list(self, data: CardPaymentList) -> PagedType[CardPaymentModel]:
        """Read matching payments with one expiry cutoff for the page.

        Args:
            data: Validated filters and paging values.

        Returns:
            The filtered page in descending identity order and its total count.
        """
        page = await self.repo.list(
            data,
            as_of=utc_now(),
            limit=data.per_page,
            offset=min((data.page - 1) * data.per_page, INT64_MAX),
        )
        return page
