"""Cache the public fields of the singleton settings using native Redis."""

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import TypeAdapter
from redis.exceptions import ConnectionError, OutOfMemoryError, TimeoutError

from ....domain.results.records import PaymentSettingsView

_snapshot = TypeAdapter(PaymentSettingsView)


class PaymentSettingsCache:
    key = "shop:payment-settings:v2"

    def __init__(self, redis: RedisClient | None) -> None:
        """Borrow the optional application Redis client."""
        self.redis = redis

    async def find(self) -> PaymentSettingsView | None:
        """Read cached settings, falling back on Redis connection errors."""
        view = None
        if self.redis is not None:
            try:
                raw = await resolve(self.redis.client.get(self.key))
                if raw is not None:
                    view = _snapshot.validate_json(raw)
            except (ConnectionError, TimeoutError):
                pass
        return view

    async def store(self, view: PaymentSettingsView, ttl: int) -> None:
        """Store the safe settings view with its expiry in seconds."""
        if self.redis is not None:
            try:
                await resolve(
                    self.redis.client.set(
                        self.key, _snapshot.dump_json(view), ex=ttl
                    )
                )
            except (ConnectionError, TimeoutError, OutOfMemoryError):
                pass

    async def forget(self) -> None:
        """Remove the settings view after a successful write."""
        if self.redis is not None:
            try:
                await resolve(self.redis.client.delete(self.key))
            except (ConnectionError, TimeoutError):
                pass
