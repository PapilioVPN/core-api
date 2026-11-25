"""Read a bounded page of stored crypto payments."""

from papilio.schemas.results import PagedType

from ...domain.dtos.search import PaymentSearch
from ...domain.models.records import CryptoPaymentModel
from ...infra.pg.repositories.crud import CryptoPaymentRepository


class CryptoPaymentSearchQuery:
    def __init__(self, repo: CryptoPaymentRepository) -> None:
        """Bind the request's native payment repository."""
        self.repo = repo

    async def search(
        self, data: PaymentSearch
    ) -> PagedType[CryptoPaymentModel]:
        """Search stored attempts without contacting any gateway.

        Args:
            data: Validated filters, page number and page size.

        Returns:
            Matching payments newest first and their total before paging.
        """
        page = await self.repo.search(
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
            gateway_id=data.gateway_id,
            status=data.status,
            amount=data.amount,
            invoice_id=data.invoice_id,
            provider_payment_id=data.provider_payment_id,
            has_invoice=data.has_invoice,
            created_since=data.created_since,
            created_until=data.created_until,
        )
        return page
