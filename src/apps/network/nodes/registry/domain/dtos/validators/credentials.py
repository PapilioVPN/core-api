"""Validate values sent as Node authentication metadata."""

from cryptography.x509 import load_pem_x509_certificates
from pydantic import SecretStr


def validate_api_key(value: SecretStr) -> SecretStr:
    """Require a nonempty value in the visible ASCII metadata range."""
    raw = value.get_secret_value()
    if not raw or any(not 33 <= ord(char) <= 126 for char in raw):
        raise ValueError("Enter a Node API key using visible ASCII characters")
    return value


def validate_ca_pem(value: str) -> str:
    """Accept a PEM certificate bundle without any private key material."""
    try:
        if "PRIVATE KEY-----" in value or not load_pem_x509_certificates(
            value.encode("ascii")
        ):
            raise ValueError
    except (UnicodeError, ValueError):
        raise ValueError(
            "Enter a PEM-encoded Node CA certificate or bundle"
        ) from None
    return value
