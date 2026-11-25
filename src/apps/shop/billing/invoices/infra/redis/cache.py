"""Store immutable previews as individual, expiring Redis hashes."""

from uuid import UUID

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import TypeAdapter, ValidationError
from redis.exceptions import RedisError

from ...domain.errors import InvoiceUnavailable
from ...domain.models.records import Invoice

_invoice = TypeAdapter(Invoice)


def _key(customer_id: int, id: UUID) -> str:
    return f"shop:billing:invoices:{customer_id}:{id}"


class InvoiceCache:
    def __init__(self, redis: RedisClient | None) -> None:
        """Borrow the native Redis connection."""
        self.redis = redis

    async def save(self, data: Invoice) -> None:
        """Store the preview and deadline in one Redis transaction."""
        redis = self.redis
        if redis is None:
            raise InvoiceUnavailable()
        key = _key(data.customer_id, data.id)
        try:
            async with redis.client.pipeline(transaction=True) as pipe:
                pipe.hset(key, "preview", _invoice.dump_json(data))
                pipe.pexpireat(key, data.expires_at)
                await pipe.execute()
        except RedisError as error:
            raise InvoiceUnavailable() from error

    async def find(self, customer_id: int, id: UUID) -> Invoice | None:
        """Read the owned snapshot or return None without extending the TTL."""
        redis = self.redis
        if redis is None:
            raise InvoiceUnavailable()
        try:
            raw = await resolve(
                redis.client.hget(_key(customer_id, id), "preview")
            )
            invoice = _invoice.validate_json(raw) if raw is not None else None
        except (RedisError, ValidationError) as error:
            raise InvoiceUnavailable() from error
        if invoice is not None and (
            invoice.id != id or invoice.customer_id != customer_id
        ):
            raise InvoiceUnavailable()
        return invoice
