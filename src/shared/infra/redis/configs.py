"""Use optional Redis for typed provider configuration views."""

from enum import StrEnum

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import BaseModel
from redis.exceptions import ConnectionError, OutOfMemoryError, TimeoutError


class ConfigCache[K: StrEnum, V: BaseModel]:
    def __init__(
        self, redis: RedisClient | None, prefix: str, model: type[V]
    ) -> None:
        self.redis = redis
        self.prefix = prefix
        self.model = model

    async def find(self, key: K) -> V | None:
        """Read the view for a provider kind, or None when unavailable."""
        record = None
        if self.redis is not None:
            try:
                raw = await resolve(
                    self.redis.client.get(f"{self.prefix}:{key}")
                )
                if raw is not None:
                    record = self.model.model_validate_json(raw)
            except (ConnectionError, TimeoutError):
                pass
        return record

    async def store(self, key: K, record: V, ttl: int) -> None:
        """Cache a materialized view for the given number of seconds."""
        if self.redis is not None:
            try:
                await resolve(
                    self.redis.client.set(
                        f"{self.prefix}:{key}",
                        record.model_dump_json(),
                        ex=ttl,
                    )
                )
            except (ConnectionError, TimeoutError, OutOfMemoryError):
                pass

    async def forget(self, key: K) -> None:
        """Evict the view for the changed provider kind."""
        if self.redis is not None:
            try:
                await resolve(self.redis.client.delete(f"{self.prefix}:{key}"))
            except (ConnectionError, TimeoutError):
                pass
