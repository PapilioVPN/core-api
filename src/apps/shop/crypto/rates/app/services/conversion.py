"""Convert rials using a verified pricing rate."""

from datetime import datetime, timedelta
from decimal import ROUND_UP, Decimal, localcontext

from ...domain.errors import RateUnavailable
from ...domain.models.records import CryptoRateModel
from ...domain.results.conversion import Conversion


class ConversionService:
    def to_usd(
        self,
        amount: int,
        rate: CryptoRateModel | None,
        *,
        now: datetime,
        max_age: timedelta,
    ) -> Conversion:
        """Convert rials at a fresh observed rate, rounding up to cents.

        Args:
            amount: Original positive amount in rials.
            rate: Stored USD proxy, expressed in rials per dollar.
            now: Aware instant against which freshness is evaluated.
            max_age: Maximum acceptable age of the observation.

        Returns:
            The USD amount and the exact rial rate applied to it.

        Raises:
            RateUnavailable: The rate is absent, stale or unusable.
        """
        if (
            rate is None
            or rate.currency != "USD"
            or rate.source != "wallex_usdt"
            or rate.fetched_at is None
            or not now - max_age <= rate.fetched_at <= now
            or not rate.rial_rate.is_finite()
            or rate.rial_rate <= 0
        ):
            raise RateUnavailable()
        with localcontext() as context:
            context.prec = 64
            converted = (Decimal(amount) / rate.rial_rate).quantize(
                Decimal("0.01"), rounding=ROUND_UP
            )
        return Conversion(amount=converted, rial_rate=rate.rial_rate)
