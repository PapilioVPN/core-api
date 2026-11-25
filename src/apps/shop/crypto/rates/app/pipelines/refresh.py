"""Use the local USDT market as a proxy for USD invoice pricing."""

from papilio.utils.dates import utc_now

from ...domain.models.records import Rate
from ..interfaces.cache import IRateCache
from ..interfaces.feed import IWallexRate


class RateRefreshPipeline:
    def __init__(self, feed: IWallexRate, cache: IRateCache) -> None:
        """Bind the public feed and latest-rate cache."""
        self.feed = feed
        self.cache = cache

    async def run(self) -> Rate:
        """Read the market, then update the cached USD pricing proxy.

        Returns:
            The saved USD pricing rate in rials per unit, with its source.

        Raises:
            RateUnavailable: The market price or Redis is unavailable.
        """
        toman_rate = await self.feed.read()
        data = Rate(
            currency="USD",
            rial_rate=toman_rate * 10,
            source="wallex_usdt",
            fetched_at=utc_now(),
        )
        rate = await self.cache.save(data)
        return rate
