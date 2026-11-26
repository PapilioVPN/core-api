"""Validate complete gateway amount bounds in whole rials."""

from papilio.errors.exceptions import ValidationException


def invalid_limits() -> ValidationException:
    """Describe an inverted interval on its two input fields."""
    return ValidationException(
        message="The minimum amount must not exceed the maximum amount.",
        message_code="invalid_gateway_limits",
        loc=["min_amount", "max_amount"],
    )


def validate_limits(min_amount: int | None, max_amount: int | None) -> None:
    """Validate the order of the supplied inclusive rial limits."""
    if (
        min_amount is not None
        and max_amount is not None
        and min_amount > max_amount
    ):
        raise invalid_limits()
