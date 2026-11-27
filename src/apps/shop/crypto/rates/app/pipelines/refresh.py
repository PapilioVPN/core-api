"""Refresh the cached USD price from the local USDT market."""

from papilio.utils.dates import utc_now

from ...domain.models.records import USD, WALLEX_USDT, Rate
from ...domain.results.records import RateFailure
from ..interfaces.cache import IRateCache
from ..interfaces.feed import IWallexRate

RIALS_PER_TOMAN = 10


class RateRefreshPipeline:
    def __init__(self, feed: IWallexRate, cache: IRateCache) -> None:
        """Bind the public feed and latest-rate cache."""
        self.feed = feed
        self.cache = cache

    async def run(self) -> Rate | RateFailure:
        """Read the market and preserve the last good rate on failure.

        Returns:
            The saved observation in rials per USD, or the failure reason.
        """
        observation = await self.feed.read()
        if isinstance(observation, RateFailure):
            result = observation
        else:
            result = await self.cache.save(
                Rate(
                    currency=USD,
                    rial_rate=observation * RIALS_PER_TOMAN,
                    source=WALLEX_USDT,
                    fetched_at=utc_now(),
                )
            )
        return result
