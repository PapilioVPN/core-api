"""Store only the safe gateway settings projection in native Redis."""

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import TypeAdapter
from redis.exceptions import ConnectionError, OutOfMemoryError, TimeoutError

from ....domain.results.configs import GatewayConfigView

_snapshot = TypeAdapter(GatewayConfigView)


class GatewayConfigCache:
    prefix = "shop:crypto-gateways:config"

    def __init__(self, redis: RedisClient | None) -> None:
        """Borrow the optional application Redis client."""
        self.redis = redis

    async def find(self, id: int) -> GatewayConfigView | None:
        """Read one panel snapshot, falling back on connection errors."""
        view = None
        if self.redis is not None:
            try:
                raw = await resolve(
                    self.redis.client.get(f"{self.prefix}:{id}")
                )
                if raw is not None:
                    view = _snapshot.validate_json(raw)
            except (ConnectionError, TimeoutError):
                pass
        return view

    async def store(self, view: GatewayConfigView, ttl: int) -> None:
        """Cache one credential-free snapshot for the given TTL in seconds."""
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
        """Evict the saved snapshot, if present."""
        if self.redis is not None:
            try:
                await resolve(self.redis.client.delete(f"{self.prefix}:{id}"))
            except (ConnectionError, TimeoutError):
                pass
