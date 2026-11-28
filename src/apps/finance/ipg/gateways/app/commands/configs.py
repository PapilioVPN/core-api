"""Replace a gateway account's complete provider configuration."""

from papilio.errors.exceptions import ValidationException

from ...domain.dtos.configs import GatewayConfig
from ...domain.models.records import GatewayModel
from ..interfaces.configs import IConfigService, IGatewayConfigCodec
from ..interfaces.services import IGatewayService


class GatewayConfigCommand:
    def __init__(
        self,
        gateways: IGatewayService,
        configs: IConfigService,
        codec: IGatewayConfigCodec,
    ) -> None:
        self.gateways = gateways
        self.configs = configs
        self.codec = codec

    async def replace(self, id: int, data: GatewayConfig) -> GatewayModel:
        """Seal the replacement credentials and update the account.

        Args:
            id: Gateway identity.
            data: Complete validated replacement settings.

        Returns:
            The updated gateway account.

        Raises:
            ValidationException: Credential encryption is unavailable.
            NotFoundException: The gateway does not exist.
        """
        config = self.codec.seal(data)
        if config is None:
            raise ValidationException(
                message="Gateway credential encryption is unavailable.",
                message_code="ipg_encryption_unavailable",
                loc=["config"],
            )
        gateway = await self.gateways.get_by_id(id)
        await self.configs.replace(gateway.kind, config)
        return gateway
