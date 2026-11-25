"""Verify the provider's recursively sorted JSON HMAC."""

from hmac import compare_digest, digest
from json import loads
from re import fullmatch

from pydantic import JsonValue

from ..json import encode_json


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    """Check the canonical SHA-512 signature."""
    valid = False
    if fullmatch(r"[0-9a-f]{128}", signature):
        try:
            payload: JsonValue = loads(body)
            if isinstance(payload, dict):
                message = encode_json(payload, sort_keys=True).encode()
                expected = digest(secret.encode(), message, "sha512").hex()
                valid = compare_digest(expected, signature)
        except (ValueError, OverflowError, RecursionError):
            pass
    return valid
