"""Validate the Node v1 rule document without normalizing its bytes."""

from pydantic_core import PydanticCustomError, from_json


def require_rule_object(value: str) -> str:
    source = value.encode("utf-8")
    if len(source) > 32 << 10:
        raise PydanticCustomError(
            "routing_rule_size", "A rule must be at most 32 KiB"
        )
    try:
        data = from_json(source, allow_inf_nan=False)
    except ValueError:
        raise PydanticCustomError(
            "routing_rule_json", "Enter a valid routing rule JSON object"
        ) from None
    if not isinstance(data, dict):
        raise PydanticCustomError(
            "routing_rule_json", "Enter a valid routing rule JSON object"
        )
    return value


def require_confirmation(value: object) -> object:
    if value is not True:
        raise PydanticCustomError(
            "routing_confirm_replace", "Confirm replacement explicitly"
        )
    return value
