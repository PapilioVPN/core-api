"""Keep the latest successful rate for each currency in Redis."""

from typing import cast

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import TypeAdapter, ValidationError
from redis.exceptions import RedisError

from ...domain.errors import RateUnavailable
from ...domain.models.records import Rate

_rate = TypeAdapter(Rate)


def _decode(currency: str, raw: str | bytes) -> Rate:
    rate = _rate.validate_json(raw)
    if rate.currency != currency:
        raise RateUnavailable()
    return rate


class RateCache:
    key = "shop:crypto:rates"

    def __init__(self, redis: RedisClient | None) -> None:
        """Borrow the application Redis client when configured."""
        self.redis = redis

    async def save(self, data: Rate) -> Rate:
        """Replace the latest observation for one pricing currency.

        Args:
            data: Rials per currency unit, with the source and fetch time.

        Returns:
            The observation now saved in Redis.

        Raises:
            RateUnavailable: The rate could not be saved in Redis.
        """
        redis = self.redis
        if redis is None:
            raise RateUnavailable()
        try:
            await resolve(
                redis.client.hset(
                    self.key, data.currency, _rate.dump_json(data)
                )
            )
        except RedisError as error:
            raise RateUnavailable() from error
        return data

    async def find(self, currency: str) -> Rate | None:
        """Read the latest observation without extending its freshness.

        Args:
            currency: Exact pricing currency code.

        Returns:
            The cached observation, or None when that currency is missing.

        Raises:
            RateUnavailable: Redis is unavailable or the rate is invalid.
        """
        redis = self.redis
        if redis is None:
            raise RateUnavailable()
        try:
            raw = await resolve(redis.client.hget(self.key, currency))
            rate = _decode(currency, raw) if raw is not None else None
        except (RedisError, ValidationError) as error:
            raise RateUnavailable() from error
        return rate

    async def find_all(self) -> list[Rate]:
        """Read the current observations without refreshing or extending them.

        Returns:
            Cached rates in currency order, empty before the first refresh.

        Raises:
            RateUnavailable: Redis is unavailable or an observation is invalid.
        """
        redis = self.redis
        if redis is None:
            raise RateUnavailable()
        try:
            values = cast(
                dict[str, str], await resolve(redis.client.hgetall(self.key))
            )
            rates = [_decode(code, values[code]) for code in sorted(values)]
        except (RedisError, ValidationError) as error:
            raise RateUnavailable() from error
        return rates
