"""Verify currency units, expiry and conversion rounding."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, Decimal, localcontext

import pytest
from papilio.types.constants import INT64_MAX

from src.apps.shop.crypto.rates.app.services.conversion import (
    ConversionService,
)
from src.apps.shop.crypto.rates.domain.models.records import Rate
from src.apps.shop.crypto.rates.domain.results.conversion import (
    Conversion,
    RialConversion,
)
from src.apps.shop.crypto.rates.domain.results.records import RateFailure

pytestmark = pytest.mark.unit
NOW = datetime(2026, 11, 27, tzinfo=UTC)
MAX_AGE = timedelta(minutes=2)
RATE = Rate("USD", Decimal("600000.1"), "wallex_usdt", NOW - MAX_AGE)


def test_convert_both_directions_with_explicit_units() -> None:
    service = ConversionService()

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        usd = service.to_usd(606_001, RATE, now=NOW, max_age=MAX_AGE)
        rials = service.to_rial(
            Decimal("1.01"), RATE, now=NOW, max_age=MAX_AGE
        )

    assert isinstance(usd, Conversion)
    assert usd.amount == Decimal("1.02")
    assert usd.rial_rate == RATE.rial_rate
    assert isinstance(rials, RialConversion)
    assert rials.amount == 606_001
    assert isinstance(rials.amount, int)
    assert rials.rial_rate == RATE.rial_rate


@pytest.mark.parametrize("amount", [0, -1, True, INT64_MAX + 1])
def test_invalid_rial_amount_is_a_validation_error(amount: int) -> None:
    result = ConversionService().to_usd(amount, RATE, now=NOW, max_age=MAX_AGE)
    assert result is RateFailure.INVALID_AMOUNT


@pytest.mark.parametrize(
    "amount", [Decimal("0"), Decimal("-1"), Decimal("NaN")]
)
def test_invalid_dollar_amount_is_a_validation_error(amount: Decimal) -> None:
    result = ConversionService().to_rial(
        amount, RATE, now=NOW, max_age=MAX_AGE
    )
    assert result is RateFailure.INVALID_AMOUNT


def test_rial_output_must_fit_the_storage_range() -> None:
    rate = replace(RATE, rial_rate=Decimal(INT64_MAX))
    result = ConversionService().to_rial(
        Decimal("1.01"), rate, now=NOW, max_age=MAX_AGE
    )
    assert result is RateFailure.INVALID_AMOUNT


@pytest.mark.parametrize(
    ("rate", "failure"),
    [
        (None, RateFailure.MISSING_RATE),
        (replace(RATE, currency="EUR"), RateFailure.INVALID_RATE),
        (replace(RATE, source="other"), RateFailure.INVALID_RATE),
        (replace(RATE, rial_rate=Decimal("0")), RateFailure.INVALID_RATE),
        (replace(RATE, rial_rate=Decimal("NaN")), RateFailure.INVALID_RATE),
        (
            replace(RATE, fetched_at=NOW.replace(tzinfo=None)),
            RateFailure.INVALID_RATE,
        ),
        (
            replace(RATE, fetched_at=NOW + timedelta(microseconds=1)),
            RateFailure.INVALID_RATE,
        ),
        (
            replace(
                RATE, fetched_at=RATE.fetched_at - timedelta(microseconds=1)
            ),
            RateFailure.STALE_RATE,
        ),
    ],
)
def test_conversion_rejects_unusable_rates(
    rate: Rate | None, failure: RateFailure
) -> None:
    service = ConversionService()
    assert service.to_usd(100_000, rate, now=NOW, max_age=MAX_AGE) is failure
    assert (
        service.to_rial(Decimal("1"), rate, now=NOW, max_age=MAX_AGE)
        is failure
    )


def test_directed_rounding_does_not_drop_a_cent() -> None:
    rate = replace(RATE, rial_rate=Decimal("9999." + "9" * 95))
    usd = ConversionService().to_usd(10_000, rate, now=NOW, max_age=MAX_AGE)
    assert isinstance(usd, Conversion)
    assert usd.amount == Decimal("1.01")
