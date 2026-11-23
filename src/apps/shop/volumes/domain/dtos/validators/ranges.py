"""Validate the selectable sizes for a custom volume."""

from papilio.errors.exceptions import ValidationException


def check_range(min_bytes: int, max_bytes: int, step_bytes: int) -> None:
    """Require a range with a maximum reachable from the minimum.

    Args:
        min_bytes: First selectable size in bytes.
        max_bytes: Last selectable size in bytes.
        step_bytes: Positive increment between adjacent selections.

    Raises:
        ValidationException: The range is empty or its maximum is unreachable.
    """
    width = max_bytes - min_bytes
    if width <= 0 or width % step_bytes:
        raise ValidationException(
            message="Maximum must be a whole number of steps above minimum",
            message_code="invalid_volume_range",
            loc=["max_bytes"],
        )
