"""Read the current storefront terms before creating a preview."""

from papilio.errors.exceptions import ForbiddenException
from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)
from src.apps.shop.products.catalogs.app.interfaces.public import (
    IPublicCatalogQuery,
)
from src.apps.shop.products.services.app.interfaces.services import (
    IShopService,
)
from src.apps.shop.products.volume_ranges.app.interfaces.queries import (
    IQuoteQuery,
)
from src.apps.shop.products.volume_ranges.domain.dtos.quote import QuoteInput

from ...domain.dtos.records import TopupInput
from ...domain.models.records import Catalog, Terms, Topup, VolumeRange


class InvoiceTermsQuery:
    def __init__(
        self,
        customers: ICustomerService,
        catalogs: IPublicCatalogQuery,
        ranges: IQuoteQuery,
        services: IShopService,
    ) -> None:
        """Bind the customer and authoritative storefront reads."""
        self.customers = customers
        self.catalogs = catalogs
        self.ranges = ranges
        self.services = services

    async def _check_customer(self, id: int) -> None:
        customer = await self.customers.get_by_id(id)
        if customer.is_blocked:
            raise ForbiddenException(
                "This customer cannot request an invoice.",
                "billing_invoice_customer_blocked",
            )

    @transactional
    async def topup(self, customer_id: int, data: TopupInput) -> Terms:
        """Prepare a top-up amount supplied in whole rials."""
        await self._check_customer(customer_id)
        return Terms(data.amount, Topup())

    @transactional
    async def catalog(self, customer_id: int, id: int) -> Terms:
        """Prepare the published catalog price and its purchase details."""
        await self._check_customer(customer_id)
        offer = await self.catalogs.get_by_id(id)
        return Terms(
            offer.price,
            Catalog(
                catalog_id=offer.id,
                service_id=offer.service_id,
                service_title=offer.service_title,
                title=offer.title,
                volume_bytes=offer.volume_bytes,
                days=offer.duration_days,
                starts_on=offer.starts_on,
            ),
        )

    @transactional
    async def range(
        self, customer_id: int, service_id: int, data: QuoteInput
    ) -> Terms:
        """Prepare the authoritative price for selected bytes and days."""
        await self._check_customer(customer_id)
        quote = await self.ranges.quote(service_id, data)
        service = await self.services.get_by_id(service_id)
        return Terms(
            quote.price,
            VolumeRange(
                range_id=quote.range_id,
                service_id=service_id,
                service_title=service.title,
                volume_bytes=quote.volume_bytes,
                days=quote.days,
            ),
        )
