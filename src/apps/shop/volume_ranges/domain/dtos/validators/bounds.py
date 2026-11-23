"""Validate the permitted steps of a volume rule."""

from papilio.errors.exceptions import ValidationException


def validate_volume(min_bytes: int, max_bytes: int, step_bytes: int) -> None:
    """Require the maximum volume to be reachable from the minimum.

    Args:
        min_bytes: Inclusive minimum volume in bytes.
        max_bytes: Inclusive maximum volume in bytes.
        step_bytes: Positive step in bytes.

    Returns:
        None.

    Raises:
        ValidationException: The maximum is below the minimum or off step.
    """
    width = max_bytes - min_bytes
    if width < 0 or width % step_bytes:
        raise ValidationException(
            message="Maximum volume must be reachable in whole steps.",
            message_code="invalid_volume_bounds",
            loc=["max_bytes"],
        )


def validate_days(
    min_days: int | None, max_days: int | None, step_days: int | None
) -> None:
    """Require all duration fields together and a reachable maximum.

    Args:
        min_days: Inclusive minimum days, or None for no expiry.
        max_days: Inclusive maximum days, or None for no expiry.
        step_days: Positive step in days, or None for no expiry.

    Returns:
        None.

    Raises:
        ValidationException: Duration fields are partial or off step.
    """
    if min_days is None and max_days is None and step_days is None:
        return
    if min_days is None or max_days is None or step_days is None:
        raise ValidationException(
            message="Supply all duration bounds or leave all of them empty.",
            message_code="incomplete_duration_bounds",
            loc=["min_days", "max_days", "step_days"],
        )
    width = max_days - min_days
    if width < 0 or width % step_days:
        raise ValidationException(
            message="Maximum duration must be reachable in whole steps.",
            message_code="invalid_duration_bounds",
            loc=["max_days"],
        )
