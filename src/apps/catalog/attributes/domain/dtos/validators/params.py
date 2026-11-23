"""Validate the attribute type used by a subscription parameter."""

from papilio.errors.exceptions import ValidationException

from src.apps.catalog.attributes.domain.enums.records import (
    AttributeType,
    ParamKey,
)


def check_param(type: AttributeType, key: ParamKey | None) -> None:
    """Accept integer attributes for duration in days and quota in bytes."""
    if key is not None and type is not AttributeType.INT:
        raise ValidationException(
            message="Subscription parameters require an integer attribute",
            message_code="invalid_param_type",
            loc=["param_key"],
        )
