"""Use native Redis hash fields for independently expiring catalog details."""

from collections.abc import Sequence

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

    async def find_many(self, ids: Sequence[int]) -> dict[int, CatalogDetail]:
        """Fetch available detail fields in one Redis operation."""
        details = {}
        if self.redis is not None and ids:
            try:
                entries = await resolve(
                    self.redis.client.hmget(self.key, [str(id) for id in ids])
                )
                details = {
                    id: _snapshot.validate_json(raw)
                    for id, raw in zip(ids, entries, strict=True)
                    if raw is not None
                }
            except (ConnectionError, TimeoutError):
                pass
        return details

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

    async def store_many(
        self, details: Sequence[CatalogDetail], ttl: int
    ) -> None:
        """Cache materialized detail fields together with individual expiry."""
        if self.redis is not None and details:
            try:
                await resolve(
                    self.redis.client.hsetex(
                        self.key,
                        mapping={
                            str(detail.catalog.id): _snapshot.dump_json(detail)
                            for detail in details
                        },
                        ex=ttl,
                    )
                )
            except (ConnectionError, TimeoutError, OutOfMemoryError):
                pass
