"""Create and read customer-bound one-hour previews."""

from datetime import timedelta
from uuid import UUID, uuid4

from papilio.errors.exceptions import NotFoundException
from papilio.utils.dates import utc_now

from ...domain.models.records import Invoice, Terms
from ...infra.redis.cache import InvoiceCache


class BillingInvoiceService:
    def __init__(self, cache: InvoiceCache) -> None:
        """Bind Redis as the source of temporary previews."""
        self.cache = cache

    async def create(self, customer_id: int, terms: Terms) -> Invoice:
        """Save the exact prepared terms for one hour.

        Args:
            customer_id: Trusted owning customer identity.
            terms: Prepared price in rials and selected purchase details.

        Returns:
            The stored preview without transferable payment instructions.
        """
        invoice = Invoice(
            id=uuid4(),
            customer_id=customer_id,
            amount=terms.amount,
            details=terms.details,
            expires_at=utc_now() + timedelta(hours=1),
        )
        await self.cache.save(invoice)
        return invoice

    async def get(self, customer_id: int, id: UUID) -> Invoice:
        """Read one preview without changing its deadline.

        Args:
            customer_id: Trusted owning customer identity.
            id: Preview identifier.

        Returns:
            The original priced preview.

        Raises:
            NotFoundException: The preview is absent, expired or not owned.
        """
        invoice = await self.cache.find(customer_id, id)
        if invoice is None or invoice.expires_at <= utc_now():
            raise NotFoundException(
                "Billing invoice preview was not found.",
                "billing_invoice_not_found",
                "BillingInvoice",
                "id",
                id,
            )
        return invoice
