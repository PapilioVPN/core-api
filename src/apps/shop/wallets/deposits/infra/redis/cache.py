"""Store a customer's top-up invoices as independently expiring fields."""

from uuid import UUID

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import TypeAdapter, ValidationError
from redis.exceptions import RedisError

from ...domain.errors import DepositInvoiceUnavailable
from ...domain.models.records import DepositInvoice

_invoice = TypeAdapter(DepositInvoice)


class WalletDepositCache:
    key = "shop:wallets:deposits"

    def __init__(self, redis: RedisClient | None) -> None:
        """Borrow the application's Redis client."""
        self.redis = redis

    async def save(self, invoice: DepositInvoice) -> DepositInvoice:
        """Save the invoice and its absolute expiry in one Redis operation.

        Args:
            invoice: Customer invoice with its amount in whole rials.

        Returns:
            The invoice saved in Redis.

        Raises:
            DepositInvoiceUnavailable: Redis could not save the invoice.
        """
        redis = self.redis
        if redis is None:
            raise DepositInvoiceUnavailable()
        try:
            await resolve(
                redis.client.hsetex(
                    f"{self.key}:{invoice.customer_id}",
                    mapping={str(invoice.id): _invoice.dump_json(invoice)},
                    exat=invoice.expires_at,
                )
            )
        except RedisError as error:
            raise DepositInvoiceUnavailable() from error
        return invoice

    async def find(self, customer_id: int, id: UUID) -> DepositInvoice | None:
        """Read an invoice from the customer's hash without renewing it.

        Args:
            customer_id: Customer that owns the invoice.
            id: Invoice UUID.

        Returns:
            The matching invoice, or None if it is missing or expired.

        Raises:
            DepositInvoiceUnavailable: Redis could not load the invoice.
        """
        redis = self.redis
        if redis is None:
            raise DepositInvoiceUnavailable()
        try:
            raw = await resolve(
                redis.client.hget(f"{self.key}:{customer_id}", str(id))
            )
            invoice = _invoice.validate_json(raw) if raw is not None else None
        except (RedisError, ValidationError) as error:
            raise DepositInvoiceUnavailable() from error
        return invoice
