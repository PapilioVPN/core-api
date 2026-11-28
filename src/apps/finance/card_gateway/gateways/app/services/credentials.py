"""Read authoritative Variza credentials for provider operations."""

from pydantic import SecretStr

from ...domain.dtos.configs import VarizaLinkConfig
from ..interfaces.configs import IConfigService, IGatewayConfigCodec
from ..interfaces.services import IGatewayService


class GatewayConfigService:
    def __init__(
        self,
        gateways: IGatewayService,
        configs: IConfigService,
        codec: IGatewayConfigCodec,
    ) -> None:
        self.gateways = gateways
        self.configs = configs
        self.codec = codec

    async def link(self, id: int) -> VarizaLinkConfig | None:
        """Read usable link settings for the specified active account."""
        gateway = await self.gateways.find_by_id(id)
        config = None
        if gateway is not None and gateway.is_active:
            record = await self.configs.find(gateway.kind)
            if record is not None:
                config = self.codec.open_link(record.config)
        return config

    async def webhook(self, id: int) -> SecretStr | None:
        """Read the current signing secret for an existing account."""
        gateway = await self.gateways.find_by_id(id)
        secret = None
        if gateway is not None:
            record = await self.configs.find(gateway.kind)
            if record is not None:
                secret = self.codec.open_webhook(record.config)
        return secret
