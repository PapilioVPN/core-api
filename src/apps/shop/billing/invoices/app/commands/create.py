"""Prepare separately priced Billing previews without issuing payments."""

from src.apps.shop.products.volume_ranges.domain.dtos.quote import QuoteInput

from ...domain.dtos.records import TopupInput
from ...domain.models.records import Invoice
from ..queries.terms import InvoiceTermsQuery
from ..services.crud import BillingInvoiceService


class BillingInvoiceCommand:
    def __init__(
        self, terms: InvoiceTermsQuery, invoices: BillingInvoiceService
    ) -> None:
        """Bind short storefront reads and the authoritative preview store."""
        self.terms = terms
        self.invoices = invoices

    async def topup(self, customer_id: int, data: TopupInput) -> Invoice:
        """Create a preview for the requested top-up amount in rials."""
        terms = await self.terms.topup(customer_id, data)
        invoice = await self.invoices.create(customer_id, terms)
        return invoice

    async def catalog(self, customer_id: int, catalog_id: int) -> Invoice:
        """Create a preview using the published catalog price."""
        terms = await self.terms.catalog(customer_id, catalog_id)
        invoice = await self.invoices.create(customer_id, terms)
        return invoice

    async def range(
        self, customer_id: int, service_id: int, data: QuoteInput
    ) -> Invoice:
        """Create a preview at the price of the selected volume and days."""
        terms = await self.terms.range(customer_id, service_id, data)
        invoice = await self.invoices.create(customer_id, terms)
        return invoice
