"""Keep the latest successful rate for each currency in Redis."""

from typing import cast

from papilio.infra.redis.client import RedisClient, resolve
from pydantic import TypeAdapter, ValidationError
from redis.exceptions import RedisError

from ...domain.models.records import Rate
from ...domain.results.records import RateFailure

_rate = TypeAdapter(Rate)


def _decode(currency: str, raw: str | bytes) -> Rate | RateFailure:
    result: Rate | RateFailure = RateFailure.INVALID_RATE
    try:
        rate = _rate.validate_json(raw)
    except ValidationError:
        pass
    else:
        if rate.currency == currency:
            result = rate
    return result


class RateCache:
    key = "shop:crypto:rates"

    def __init__(self, redis: RedisClient | None) -> None:
        """Borrow the application Redis client when configured."""
        self.redis = redis

    async def save(self, data: Rate) -> Rate | RateFailure:
        """Save the latest observation or return a cache failure.

        Args:
            data: Rials per currency unit, with the source and fetch time.

        Returns:
            The saved observation, or a cache failure.
        """
        result: Rate | RateFailure = RateFailure.CACHE_UNAVAILABLE
        if self.redis is not None:
            try:
                await resolve(
                    self.redis.client.hset(
                        self.key, data.currency, _rate.dump_json(data)
                    )
                )
            except RedisError:
                pass
            else:
                result = data
        return result

    async def find(self, currency: str) -> Rate | RateFailure | None:
        """Read the latest observation without extending its freshness.

        Args:
            currency: Exact pricing currency code.

        Returns:
            An observation, None for an absent key, or a failure.
        """
        result: Rate | RateFailure | None = RateFailure.CACHE_UNAVAILABLE
        if self.redis is not None:
            try:
                raw = await resolve(self.redis.client.hget(self.key, currency))
            except RedisError:
                pass
            else:
                result = _decode(currency, raw) if raw is not None else None
        return result

    async def find_all(self) -> list[Rate] | RateFailure:
        """Read observations without refreshing or extending them.

        Returns:
            Cached observations in currency order or a failure.
        """
        result: list[Rate] | RateFailure = RateFailure.CACHE_UNAVAILABLE
        if self.redis is not None:
            try:
                values = cast(
                    dict[str, str],
                    await resolve(self.redis.client.hgetall(self.key)),
                )
            except RedisError:
                pass
            else:
                rates: list[Rate] = []
                result = rates
                for currency in sorted(values):
                    rate = _decode(currency, values[currency])
                    if isinstance(rate, RateFailure):
                        result = rate
                        break
                    rates.append(rate)
        return result
