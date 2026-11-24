"""Page current payments using the administrator's filters."""

from papilio.schemas.results import PagedType

from ...domain.dtos.search import PaymentSearch
from ...domain.models.records import PaymentModel
from ...infra.pg.repositories.crud import PaymentRepository


class PaymentSearchQuery:
    def __init__(self, repo: PaymentRepository) -> None:
        """Bind the request's payment repository."""
        self.repo = repo

    async def search(self, data: PaymentSearch) -> PagedType[PaymentModel]:
        """Read matching payments without loading their receipt details.

        Args:
            data: Paging, state, expected rial amount and creation bounds.

        Returns:
            Matching payments in descending identity order and their total.
        """
        page = await self.repo.search(
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
            status=data.status,
            amount=data.amount,
            created_since=data.created_since,
            created_until=data.created_until,
        )
        return page
