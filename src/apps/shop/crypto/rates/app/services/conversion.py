"""Convert between whole rials and USD using a verified pricing rate."""

from datetime import UTC, datetime, timedelta
from decimal import ROUND_UP, Context, Decimal, DecimalException, localcontext

from papilio.types.constants import INT64_MAX

from ...domain.models.records import USD, WALLEX_USDT, Rate
from ...domain.results.conversion import (
    CONVERSION_PRECISION,
    RIAL_UNIT,
    USD_CENT,
    Conversion,
    RialConversion,
)
from ...domain.results.records import RateFailure


class ConversionService:
    def to_usd(
        self,
        amount: int,
        rate: Rate | None,
        *,
        now: datetime,
        max_age: timedelta,
    ) -> Conversion | RateFailure:
        """Convert an amount due in whole rials, rounding up to USD cents.

        Args:
            amount: The original positive BIGINT amount in rials.
            rate: USD proxy in rials per dollar, when available.
            now: Aware instant used to evaluate the observation age.
            max_age: Maximum acceptable age, inclusive.

        Returns:
            The USD amount and exact applied rate, or the failure reason.
        """
        result: Conversion | RateFailure = RateFailure.INVALID_AMOUNT
        if type(amount) is int and 0 < amount <= INT64_MAX:
            rial_rate = self._usd_rate(rate, now=now, max_age=max_age)
            if isinstance(rial_rate, RateFailure):
                result = rial_rate
            else:
                try:
                    with localcontext(
                        Context(prec=CONVERSION_PRECISION, rounding=ROUND_UP)
                    ):
                        converted = (Decimal(amount) / rial_rate).quantize(
                            USD_CENT
                        )
                except DecimalException:
                    result = RateFailure.INVALID_RATE
                else:
                    result = Conversion(amount=converted, rial_rate=rial_rate)
        return result

    def to_rial(
        self,
        amount: Decimal,
        rate: Rate | None,
        *,
        now: datetime,
        max_age: timedelta,
    ) -> RialConversion | RateFailure:
        """Convert a positive USD amount due, rounding up to whole rials.

        Args:
            amount: The original finite positive USD amount.
            rate: USD proxy in rials per dollar, when available.
            now: Aware instant used to evaluate the observation age.
            max_age: Maximum acceptable age, inclusive.

        Returns:
            The amount due in whole rials and applied rate, or the failure.
        """
        result: RialConversion | RateFailure = RateFailure.INVALID_AMOUNT
        if amount.is_finite() and amount > 0:
            rial_rate = self._usd_rate(rate, now=now, max_age=max_age)
            if isinstance(rial_rate, RateFailure):
                result = rial_rate
            else:
                try:
                    with localcontext(
                        Context(prec=CONVERSION_PRECISION, rounding=ROUND_UP)
                    ):
                        converted = (amount * rial_rate).quantize(RIAL_UNIT)
                except DecimalException:
                    result = RateFailure.INVALID_AMOUNT
                else:
                    if 0 < converted <= INT64_MAX:
                        result = RialConversion(
                            amount=int(converted), rial_rate=rial_rate
                        )
        return result

    @staticmethod
    def _usd_rate(
        rate: Rate | None, *, now: datetime, max_age: timedelta
    ) -> Decimal | RateFailure:
        """Select a fresh observation from the configured USD proxy source."""
        result: Decimal | RateFailure = RateFailure.INVALID_RATE
        if rate is None:
            result = RateFailure.MISSING_RATE
        elif (
            rate.currency == USD
            and rate.source == WALLEX_USDT
            and now.utcoffset() is not None
            and rate.fetched_at.utcoffset() is not None
            and rate.rial_rate.is_finite()
            and rate.rial_rate > 0
        ):
            age = now.astimezone(UTC) - rate.fetched_at.astimezone(UTC)
            if timedelta(0) <= age <= max_age:
                result = rate.rial_rate
            elif age > max_age:
                result = RateFailure.STALE_RATE
        return result
