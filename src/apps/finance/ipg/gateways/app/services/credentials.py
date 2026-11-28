"""Read authoritative credentials for issuing a payment."""

from ...domain.enums.records import GatewayKind
from ...domain.results.configs import Merchant
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

    async def merchant(self, kind: GatewayKind) -> Merchant | None:
        """Read the merchant credential of an active gateway.

        Args:
            kind: Provider kind selected by the caller.

        Returns:
            The gateway identity and merchant credential, if available.
        """
        gateway = await self.gateways.find_by_kind(kind)
        merchant = None
        if gateway is not None and gateway.is_active:
            config = await self.configs.find(gateway.kind)
            credential = (
                self.codec.open(config.config) if config is not None else None
            )
            if credential is not None:
                merchant = Merchant(gateway_id=gateway.id, id=credential)
        return merchant
