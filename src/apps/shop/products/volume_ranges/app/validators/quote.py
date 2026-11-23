"""Check selected volume and duration against a stored range."""

from papilio.errors.exceptions import ValidationException

from src.apps.shop.products.volume_ranges.domain.dtos.quote import QuoteInput
from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)


def validate_quote(rule: VolumeRangeModel, data: QuoteInput) -> None:
    """Check the steps and optional expiry of the selected volume.

    Args:
        rule: Visible rule whose volume bounds contain the requested bytes.
        data: Selected volume and optional number of days.

    Returns:
        None.

    Raises:
        ValidationException: The volume or duration is not a valid choice.
    """
    if (data.volume_bytes - rule.min_bytes) % rule.step_bytes:
        raise ValidationException(
            message="The selected volume is off step.",
            message_code="invalid_volume_selection",
            loc=["volume_bytes"],
        )
    days = data.days
    minimum, maximum, step = rule.min_days, rule.max_days, rule.step_days
    if minimum is None:
        valid = days is None
    else:
        valid = (
            days is not None
            and maximum is not None
            and step is not None
            and minimum <= days <= maximum
            and (days - minimum) % step == 0
        )
    if not valid:
        raise ValidationException(
            message="The selected duration is not offered for this volume.",
            message_code="invalid_duration_selection",
            loc=["days"],
        )
