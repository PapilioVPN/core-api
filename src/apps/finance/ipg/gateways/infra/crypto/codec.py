"""Encrypt merchant credentials with the existing Papilio deployment key."""

from papilio.core.config import CryptoConfig
from papilio.security.crypto import decrypt, encrypt
from pydantic import JsonValue, SecretStr, TypeAdapter

from ...domain.dtos.configs import GatewayConfig

_SAMPLE_KEY = "replace-with-private-encryption-key"
_CIPHERTEXT = TypeAdapter(str)


class GatewayConfigCodec:
    def __init__(self, crypto: CryptoConfig | None) -> None:
        key = crypto.encryption_key if crypto is not None else ""
        self.key = key if key.strip() not in {"", _SAMPLE_KEY} else None

    def seal(self, data: GatewayConfig) -> dict[str, JsonValue] | None:
        """Prepare the provider configuration for JSONB storage.

        Args:
            data: Validated merchant credential.

        Returns:
            Encrypted configuration, or None without a deployment key.
        """
        config: dict[str, JsonValue] | None = None
        if self.key is not None:
            merchant_id = encrypt(
                data.merchant_id.get_secret_value(), self.key
            )
            config = {"merchant_id": merchant_id}
        return config

    def open(self, config: dict[str, JsonValue]) -> SecretStr | None:
        """Recover the merchant credential from authenticated storage.

        Args:
            config: Stored JSONB provider configuration.

        Returns:
            The decrypted credential, or None when it cannot be recovered.
        """
        merchant = None
        if self.key is not None:
            try:
                token = _CIPHERTEXT.validate_python(
                    config.get("merchant_id"), strict=True
                )
                value = decrypt(token, self.key)
                if value:
                    merchant = SecretStr(value)
            except ValueError:
                pass
        return merchant
