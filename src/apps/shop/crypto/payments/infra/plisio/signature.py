"""Authenticate Plisio's ordered JSON callback body."""

from hmac import compare_digest, digest
from json import loads
from re import fullmatch

from papilio.errors.exceptions import UnAuthorizedException
from pydantic import JsonValue

from ..json import encode_json
from .schemas import NoticeIn


def decode_notice(body: bytes, secret: str) -> NoticeIn:
    """Check the signed object before using its notice fields."""
    try:
        payload: JsonValue = loads(body)
        if not isinstance(payload, dict):
            raise ValueError("Expected an object")
        signature = payload.pop("verify_hash", None)
        if not isinstance(signature, str) or not fullmatch(
            r"[a-f0-9]{40}", signature
        ):
            raise ValueError("Missing callback signature")
        message = encode_json(payload, sort_keys=False).encode()
        expected = digest(secret.encode(), message, "sha1").hex()
        if not compare_digest(expected, signature):
            raise ValueError("Incorrect callback signature")
        notice = NoticeIn.model_validate(payload)
    except (ValueError, OverflowError, RecursionError):
        raise UnAuthorizedException(
            "Invalid payment notification.", "invalid_crypto_ipn"
        ) from None
    return notice
