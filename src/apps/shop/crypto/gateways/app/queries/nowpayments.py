"""Load NOWPayments credentials from the owning gateway account."""

from papilio.core.config import CryptoConfig

from ...domain.dtos.configs import NowPaymentsConfig
from ...domain.results.configs import ConfigFailure
from ...infra.crypto.codec import decode_nowpayments
from ..interfaces.configs import IGatewayConfigService


class NowPaymentsConfigQuery:
    def __init__(
        self, configs: IGatewayConfigService, crypto: CryptoConfig
    ) -> None:
        """Bind the account settings and deployment encryption key."""
        self.configs = configs
        self.crypto = crypto

    async def find(self, id: int) -> NowPaymentsConfig | ConfigFailure | None:
        """Read one account's settings for an internal provider call.

        Args:
            id: Owning gateway account identity.

        Returns:
            Validated credentials or the appropriate unavailable result.
        """
        record = await self.configs.find(id)
        config = decode_nowpayments(record, self.crypto.encryption_key)
        return config
