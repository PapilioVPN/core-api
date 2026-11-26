"""Load NOWPayments credentials from the owning gateway account."""

from papilio.core.config import CryptoConfig
from papilio.security.crypto import decrypt
from pydantic import ValidationError

from ...domain.dtos.configs import NowPaymentsConfig
from ...domain.errors import ConfigUnavailable
from ..interfaces.configs import IGatewayConfigService


class NowPaymentsConfigQuery:
    def __init__(
        self, configs: IGatewayConfigService, crypto: CryptoConfig
    ) -> None:
        """Bind the account settings and deployment encryption key."""
        self.configs = configs
        self.crypto = crypto

    async def get(self, id: int) -> NowPaymentsConfig:
        """Return authoritative NOWPayments settings for a gateway ID.

        Args:
            id: Owning gateway account identity.

        Returns:
            Settings with decrypted credentials for internal use.

        Raises:
            ConfigUnavailable: Stored settings cannot be used.
        """
        config = await self.find(id)
        if config is None:
            raise ConfigUnavailable()
        return config

    async def find(self, id: int) -> NowPaymentsConfig | None:
        """Find configured credentials without turning absence into an error.

        Args:
            id: Owning gateway account identity.

        Returns:
            The internal credentials, or None if no NOWPayments settings exist.

        Raises:
            ConfigUnavailable: Existing credentials cannot be read.
        """
        record = await self.configs.find(id)
        config = None
        if record is not None and "ipn_secret" in record.config:
            data = record.config
            key, secret = data.get("api_key"), data.get("ipn_secret")
            if not isinstance(key, str) or not isinstance(secret, str):
                raise ConfigUnavailable()
            try:
                config = NowPaymentsConfig.model_validate(
                    {
                        "kind": "nowpayments",
                        "api_url": data.get("api_url"),
                        "callback_url": data.get("callback_url"),
                        "api_key": decrypt(key, self.crypto.encryption_key),
                        "ipn_secret": decrypt(
                            secret, self.crypto.encryption_key
                        ),
                    }
                )
            except (ValidationError, ValueError) as error:
                raise ConfigUnavailable() from error
        return config
