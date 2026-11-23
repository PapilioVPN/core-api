"""Price a permitted volume and check the configured sales bounds."""

from papilio.errors.exceptions import ValidationException
from papilio.types.constants import INT64_MAX

from src.apps.shop.products.volume_ranges.domain.types.records import (
    GIB,
    MIN_PRICE,
)


def price_for(volume_bytes: int, price_per_gib: int) -> int:
    """Calculate the whole-GiB price in rials.

    Args:
        volume_bytes: Selected volume in whole GiB, expressed in bytes.
        price_per_gib: Positive rate in rials per GiB.

    Returns:
        The exact integer rial price.
    """
    return (volume_bytes // GIB) * price_per_gib


def validate_price(min_bytes: int, max_bytes: int, price_per_gib: int) -> None:
    """Check the cheapest and most expensive allowed volumes.

    Args:
        min_bytes: Minimum selectable volume.
        max_bytes: Maximum selectable volume.
        price_per_gib: Rate applied to all selectable volumes.

    Returns:
        None.

    Raises:
        ValidationException: A resulting price is outside the rial bounds.
    """
    if (
        price_for(min_bytes, price_per_gib) < MIN_PRICE
        or price_for(max_bytes, price_per_gib) > INT64_MAX
    ):
        raise ValidationException(
            message="A selectable price falls outside the rial bounds.",
            message_code="invalid_range_price",
            loc=["price_per_gib"],
        )
