"""Use the local USDT market as a proxy for USD invoice pricing."""

from papilio.infra.db.transaction import active_transaction, transaction
from papilio.utils.dates import utc_now

from ...domain.models.records import CryptoRateModel
from ..interfaces.feed import IWallexRate
from ..interfaces.services import ICryptoRateService


class RateRefreshCommand:
    def __init__(self, feed: IWallexRate, rates: ICryptoRateService) -> None:
        """Bind the public market feed and the owning record service."""
        self.feed = feed
        self.rates = rates

    async def refresh(self) -> CryptoRateModel:
        """Refresh the USD proxy without holding SQL during the market call.

        Returns:
            The saved USD pricing rate in rials per unit, with its source.

        Raises:
            RateUnavailable: The market did not give a usable USDT price.
            RuntimeError: The caller already has an active transaction.
        """
        if active_transaction() is not None:
            raise RuntimeError("Rate refresh requires its own SQL phase")
        toman_rate = await self.feed.read()
        data = CryptoRateModel(
            currency="USD",
            rial_rate=toman_rate * 10,
            source="wallex_usdt",
            fetched_at=utc_now(),
        )
        async with transaction():
            rate = await self.rates.save(data)
        return rate
