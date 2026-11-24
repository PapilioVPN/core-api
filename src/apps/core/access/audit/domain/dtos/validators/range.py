"""Time-bound validation for audit filters."""

from datetime import datetime

from papilio.errors.exceptions import ValidationException


def check_range(since: datetime | None, until: datetime | None) -> None:
    """Validate the inclusive lower and exclusive upper time filters."""
    if since is not None and until is not None and until <= since:
        raise ValidationException(
            message="Until must be after since",
            message_code="invalid_audit_range",
            loc=["until"],
        )
