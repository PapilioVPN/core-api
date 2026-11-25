"""Read Plisio credentials for internal provider calls."""

from papilio.core.config import CryptoConfig
from papilio.security.crypto import decrypt
from pydantic import ValidationError

from ...domain.dtos.configs import PlisioConfig
from ...domain.errors import ConfigUnavailable
from ...domain.results.configs import plisio_currency
from ..interfaces.configs import IGatewayConfigService


class PlisioConfigQuery:
    def __init__(
        self, configs: IGatewayConfigService, crypto: CryptoConfig
    ) -> None:
        """Bind authoritative settings and the deployment encryption key."""
        self.configs = configs
        self.crypto = crypto

    async def get(self, id: int) -> PlisioConfig:
        """Read one Plisio account's settings without using the panel cache.

        Args:
            id: Plisio gateway account identity.

        Returns:
            Validated provider settings with an unwrapped connection key.

        Raises:
            ConfigUnavailable: Stored settings cannot be used.
        """
        record = await self.configs.find(id)
        key = record.config.get("api_key") if record is not None else None
        if record is None or not isinstance(key, str) or not key:
            raise ConfigUnavailable()
        try:
            config = PlisioConfig.model_validate(
                {
                    "kind": "plisio",
                    "api_url": record.config.get("api_url"),
                    "api_key": decrypt(key, self.crypto.encryption_key),
                    "price_currency": plisio_currency(record),
                }
            )
        except (ValidationError, ValueError):
            raise ConfigUnavailable() from None
        return config
