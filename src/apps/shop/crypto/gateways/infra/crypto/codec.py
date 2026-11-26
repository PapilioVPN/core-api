"""Encode provider connection settings for encrypted storage."""

from papilio.security.crypto import encrypt
from pydantic import JsonValue

from ...domain.dtos.configs import ConfigWrite
from ...domain.errors import ConfigUnavailable

_SAMPLE_KEY = "replace-with-private-encryption-key"


def encode(data: ConfigWrite, key: str) -> dict[str, JsonValue]:
    """Encrypt credential fields while preserving account metadata.

    Args:
        data: Validated provider configuration.
        key: Deployment encryption key.

    Returns:
        JSON-compatible account settings with encrypted credentials.

    Raises:
        ConfigUnavailable: The deployment key is not configured.
    """
    if not key.strip() or key == _SAMPLE_KEY:
        raise ConfigUnavailable()
    config: dict[str, JsonValue] = {
        "api_url": data.api_url,
        "api_key": encrypt(data.api_key.get_secret_value(), key),
    }
    if data.kind == "nowpayments":
        config["ipn_secret"] = encrypt(data.ipn_secret.get_secret_value(), key)
        if data.callback_url is not None:
            config["callback_url"] = str(data.callback_url)
    else:
        config["price_currency"] = data.price_currency
    return config
