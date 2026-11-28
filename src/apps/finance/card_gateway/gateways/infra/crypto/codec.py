"""Encrypt Variza credentials with the existing Papilio deployment key."""

from papilio.core.config import CryptoConfig
from papilio.security.crypto import decrypt, encrypt
from pydantic import JsonValue, SecretStr, TypeAdapter

from ...domain.dtos.configs import VarizaConfig, VarizaLinkConfig

_SAMPLE_KEY = "replace-with-private-encryption-key"
_CIPHERTEXT = TypeAdapter(str)


class GatewayConfigCodec:
    def __init__(self, crypto: CryptoConfig | None) -> None:
        key = crypto.encryption_key if crypto is not None else ""
        self.key = key if key.strip() and key != _SAMPLE_KEY else None

    def seal(self, data: VarizaConfig) -> dict[str, JsonValue] | None:
        """Prepare the complete provider configuration for JSONB storage.

        Args:
            data: Validated settings and exact credentials.

        Returns:
            Stored settings with encrypted credentials, or None when the
            deployment has no private encryption key.
        """
        config: dict[str, JsonValue] | None = None
        if self.key is not None:
            config = {
                "api_key": encrypt(data.api_key.get_secret_value(), self.key),
                "webhook_secret": encrypt(
                    data.webhook_secret.get_secret_value(), self.key
                ),
                "card_last_4": data.card_last_4,
                "expires_in": data.expires_in,
            }
        return config

    def open_link(
        self, config: dict[str, JsonValue]
    ) -> VarizaLinkConfig | None:
        """Materialize only the credentials and options used for link creation.

        Args:
            config: The gateway account's stored JSONB configuration.

        Returns:
            Typed link settings, or None when the configuration is unusable.
        """
        settings = None
        key = self._open(config.get("api_key"))
        if key is not None:
            try:
                settings = VarizaLinkConfig.model_validate(
                    {
                        "api_key": key,
                        "card_last_4": config.get("card_last_4"),
                        "expires_in": config.get("expires_in"),
                    }
                )
            except ValueError:
                pass
        return settings

    def open_webhook(self, config: dict[str, JsonValue]) -> SecretStr | None:
        """Recover only the secret used for webhook authentication.

        Args:
            config: Stored gateway configuration.

        Returns:
            The recovered secret or None when it is unavailable.
        """
        secret = self._open(config.get("webhook_secret"))
        return SecretStr(secret) if secret else None

    def _open(self, data: JsonValue) -> str | None:
        """Recover an authenticated credential from stored JSON."""
        value = None
        if self.key is not None:
            try:
                token = _CIPHERTEXT.validate_python(data, strict=True)
                value = decrypt(token, self.key)
            except ValueError:
                pass
        return value
