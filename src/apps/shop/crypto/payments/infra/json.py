"""Match JavaScript JSON serialization for provider signatures."""

from decimal import Decimal
from json import dumps
from math import isfinite

from pydantic import JsonValue


def _number(value: int | float) -> str:
    """Format parsed numbers using JSON.stringify's decimal thresholds."""
    if isinstance(value, int):
        value = float(value)
    if not isfinite(value):
        raise ValueError("Invalid JSON number")
    number = Decimal(repr(value)).normalize()
    if not number:
        result = "0"
    elif -6 <= number.adjusted() < 21:
        result = format(number, "f")
    else:
        coefficient, _, exponent = format(number, "e").partition("e")
        shift = int(exponent)
        result = (
            f"{coefficient}e{shift:+d}"
            if shift >= 0
            else f"{coefficient}e{shift}"
        )
    return result


def encode_json(value: JsonValue, *, sort_keys: bool) -> str:
    """Encode the signed JSON shape without adding insignificant spacing."""
    if isinstance(value, dict):
        keys = (
            sorted(value, key=lambda key: key.encode("utf-16-be"))
            if sort_keys
            else value
        )
        fields = (
            dumps(key, ensure_ascii=False)
            + ":"
            + encode_json(value[key], sort_keys=sort_keys)
            for key in keys
        )
        result = "{" + ",".join(fields) + "}"
    elif isinstance(value, list):
        result = (
            "["
            + ",".join(
                encode_json(item, sort_keys=sort_keys) for item in value
            )
            + "]"
        )
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        result = _number(value)
    else:
        result = dumps(value, ensure_ascii=False)
    return result
