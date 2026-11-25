"""Use the local USDT market as a proxy for USD invoice pricing."""

from papilio.utils.dates import utc_now

from ...domain.models.records import CryptoRateModel
from ..interfaces.feed import IWallexRate
from ..interfaces.refresh import IRateRefreshExecution


class RateRefreshPipeline:
    def __init__(
        self, feed: IWallexRate, execution: IRateRefreshExecution
    ) -> None:
        """Bind the public feed and the short persistence phase."""
        self.feed = feed
        self.execution = execution

    async def run(self) -> CryptoRateModel:
        """Read the market, then save its USD pricing proxy.

        Returns:
            The saved USD pricing rate in rials per unit, with its source.

        Raises:
            RateUnavailable: The market did not give a usable USDT price.
        """
        toman_rate = await self.feed.read()
        data = CryptoRateModel(
            currency="USD",
            rial_rate=toman_rate * 10,
            source="wallex_usdt",
            fetched_at=utc_now(),
        )
        rate = await self.execution.complete(data)
        return rate
