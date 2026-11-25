"""Cache safe gateway settings by account identity."""

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import TypeAdapter, ValidationError
from redis.exceptions import ConnectionError, OutOfMemoryError, TimeoutError

from ....domain.results.configs import GatewayConfigView

_snapshot = TypeAdapter(GatewayConfigView)


class GatewayConfigCache:
    prefix = "shop:crypto-gateways:config"

    def __init__(self, redis: RedisClient | None) -> None:
        """Borrow the optional Redis client."""
        self.redis = redis

    async def find(self, id: int) -> GatewayConfigView | None:
        """Read one safe view, or None on a miss or unavailable Redis."""
        view = None
        if self.redis is not None:
            try:
                raw = await resolve(
                    self.redis.client.get(f"{self.prefix}:{id}")
                )
                if raw is not None:
                    view = _snapshot.validate_json(raw)
            except (ConnectionError, TimeoutError, ValidationError):
                pass
        return view

    async def store(self, view: GatewayConfigView, ttl: int) -> None:
        """Cache a safe view for the supplied number of seconds."""
        if self.redis is not None:
            try:
                await resolve(
                    self.redis.client.set(
                        f"{self.prefix}:{view.gateway_id}",
                        _snapshot.dump_json(view),
                        ex=ttl,
                    )
                )
            except (ConnectionError, TimeoutError, OutOfMemoryError):
                pass

    async def forget(self, id: int) -> None:
        """Evict one account's safe view."""
        if self.redis is not None:
            try:
                await resolve(self.redis.client.delete(f"{self.prefix}:{id}"))
            except (ConnectionError, TimeoutError):
                pass
