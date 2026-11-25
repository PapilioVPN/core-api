"""Verify the provider's recursively sorted JSON HMAC."""

from decimal import Decimal
from hmac import compare_digest, digest
from json import dumps, loads
from math import isfinite
from re import fullmatch

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


def _canonical(value: JsonValue) -> str:
    """Encode the signed JSON shape without adding insignificant spacing."""
    if isinstance(value, dict):
        fields = (
            f"{dumps(key, ensure_ascii=False)}:{_canonical(value[key])}"
            for key in sorted(value, key=lambda key: key.encode("utf-16-be"))
        )
        result = "{" + ",".join(fields) + "}"
    elif isinstance(value, list):
        result = "[" + ",".join(_canonical(item) for item in value) + "]"
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        result = _number(value)
    else:
        result = dumps(value, ensure_ascii=False)
    return result


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    """Check the canonical SHA-512 signature."""
    valid = False
    if fullmatch(r"[0-9a-f]{128}", signature):
        try:
            payload: JsonValue = loads(body)
            if isinstance(payload, dict):
                message = _canonical(payload).encode()
                expected = digest(secret.encode(), message, "sha512").hex()
                valid = compare_digest(expected, signature)
        except (ValueError, OverflowError, RecursionError):
            pass
    return valid
