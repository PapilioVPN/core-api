"""Use native Redis hash fields for independently expiring catalog details."""

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import TypeAdapter
from redis.exceptions import ConnectionError, OutOfMemoryError, TimeoutError

from src.apps.shop.catalogs.domain.results.details import CatalogDetail

_snapshot = TypeAdapter(CatalogDetail)


class CatalogCache:
    key = "shop:catalog-details:v1"

    def __init__(self, redis: RedisClient | None) -> None:
        """Borrow the optional application Redis client."""
        self.redis = redis

    async def find(self, id: int) -> CatalogDetail | None:
        """Read one cached detail, treating Redis connection errors as misses.

        Args:
            id: Stored catalog identity.

        Returns:
            The stored detail or None when the cache misses or is unavailable.
        """
        detail = None
        if self.redis is not None:
            try:
                raw = await resolve(self.redis.client.hget(self.key, str(id)))
                if raw is not None:
                    detail = _snapshot.validate_json(raw)
            except (ConnectionError, TimeoutError):
                pass
        return detail

    async def store(self, detail: CatalogDetail, ttl: int) -> None:
        """Store one detail with its own expiration.

        Args:
            detail: Materialized catalog detail ready for serialization.
            ttl: Positive expiry interval in seconds.
        """
        if self.redis is not None:
            try:
                await resolve(
                    self.redis.client.hsetex(
                        self.key,
                        mapping={
                            str(detail.catalog.id): _snapshot.dump_json(detail)
                        },
                        ex=ttl,
                    )
                )
            except (ConnectionError, TimeoutError, OutOfMemoryError):
                pass

    async def forget(self, id: int) -> None:
        """Forget a committed catalog's cached detail.

        Args:
            id: Identity of the actual changed catalog.
        """
        if self.redis is not None:
            try:
                await resolve(self.redis.client.hdel(self.key, str(id)))
            except (ConnectionError, TimeoutError):
                pass
