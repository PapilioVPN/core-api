"""Read Plisio credentials for internal provider calls."""

from papilio.core.config import CryptoConfig

from ...domain.dtos.configs import PlisioConfig
from ...domain.results.configs import ConfigFailure
from ...infra.crypto.codec import decode_plisio
from ..interfaces.configs import IGatewayConfigService


class PlisioConfigQuery:
    def __init__(
        self, configs: IGatewayConfigService, crypto: CryptoConfig
    ) -> None:
        """Bind authoritative settings and the deployment encryption key."""
        self.configs = configs
        self.crypto = crypto

    async def get(self, id: int) -> PlisioConfig | ConfigFailure:
        """Read one account's settings for an internal provider call.

        Args:
            id: Owning gateway account identity.

        Returns:
            Validated credentials or the appropriate unavailable result.
        """
        record = await self.configs.find(id)
        config = decode_plisio(record, self.crypto.encryption_key)
        return config
