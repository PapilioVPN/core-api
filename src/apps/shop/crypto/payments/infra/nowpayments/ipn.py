"""Authenticate NOWPayments notifications before using their contents."""

from decimal import Decimal
from hmac import compare_digest, digest
from re import Match, compile

from orjson import OPT_SORT_KEYS, dumps
from pydantic import JsonValue

_tokens = compile(rb'"(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?(?:e[+-]?\d+)?')


def verify(data: dict[str, JsonValue], signature: str, secret: str) -> bool:
    """Compare the HMAC-SHA512 of the canonical notification body."""
    valid = False
    try:
        body = _tokens.sub(_number, dumps(data, option=OPT_SORT_KEYS))
    except TypeError:
        pass
    else:
        expected = digest(secret.strip().encode(), body, "sha512").hex()
        valid = compare_digest(expected.encode(), signature.encode())
    return valid


def _number(match: Match[bytes]) -> bytes:
    """Use JSON.stringify notation for decimal values in signed payloads."""
    token = match[0]
    if not token.startswith(b'"') and (b"." in token or b"e" in token):
        value = Decimal(token.decode())
        if value == 0:
            token = b"0"
        elif Decimal("0.000001") <= abs(value) < Decimal("1e21"):
            token = format(value.normalize(), "f").encode()
    return token
