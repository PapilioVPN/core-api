"""Own expiring wallet top-up invoices."""

from datetime import datetime
from uuid import UUID, uuid4

from papilio.tools.checks import Checks
from papilio.utils.dates import utc_now

from ...domain.models.records import DepositInvoice, DepositPayment
from ...infra.redis.cache import WalletDepositCache
from ..policy import INVOICE_TTL


class WalletDepositService(Checks[DepositInvoice]):
    entity = "DepositInvoice"

    def __init__(self, cache: WalletDepositCache) -> None:
        """Bind the cache that owns the invoice lifetime."""
        self.cache = cache

    async def create(
        self,
        customer_id: int,
        amount: int,
        payment: DepositPayment,
        *,
        created_at: datetime | None = None,
    ) -> DepositInvoice:
        """Store a prepared top-up invoice for one hour.

        Args:
            customer_id: Verified customer identity.
            amount: Original top-up amount in whole rials.
            payment: Frozen payment instructions and price.
            created_at: Start of the payment window, or the current UTC time.

        Returns:
            The cached invoice with its UUID and expiration.

        Raises:
            DepositInvoiceUnavailable: The invoice could not be stored.
        """
        issued_at = (created_at or utc_now()).replace(microsecond=0)
        invoice = await self.cache.save(
            DepositInvoice(
                id=uuid4(),
                customer_id=customer_id,
                amount=amount,
                created_at=issued_at,
                expires_at=issued_at + INVOICE_TTL,
                payment=payment,
            )
        )
        return invoice

    async def get_by_id(self, customer_id: int, id: UUID) -> DepositInvoice:
        """Read an unexpired invoice owned by the customer.

        Args:
            customer_id: Owning customer identity.
            id: Invoice UUID.

        Returns:
            The cached invoice.

        Raises:
            NotFoundException: The invoice is expired or absent.
            DepositInvoiceUnavailable: The invoice could not be loaded.
        """
        invoice = await self.cache.find(customer_id, id)
        return self._check_for_existence("id", id, invoice)
