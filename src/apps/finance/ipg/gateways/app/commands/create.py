"""Create one gateway account with credentials sealed before persistence."""

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional

from ...domain.dtos.records import GatewayCreate
from ...domain.models.configs import ConfigModel
from ...domain.models.records import GatewayModel
from ..interfaces.configs import IConfigService, IGatewayConfigCodec
from ..interfaces.services import IGatewayService


class GatewayCreateCommand:
    def __init__(
        self,
        gateways: IGatewayService,
        configs: IConfigService,
        codec: IGatewayConfigCodec,
    ) -> None:
        self.gateways = gateways
        self.configs = configs
        self.codec = codec

    @transactional
    async def create(self, data: GatewayCreate) -> GatewayModel:
        """Prepare and store a new gateway.

        Args:
            data: Validated account metadata and provider configuration.

        Returns:
            The stored gateway account.

        Raises:
            ValidationException: Credential encryption is unavailable.
        """
        config = self.codec.seal(data.config)
        if config is None:
            raise ValidationException(
                message="Gateway credential encryption is unavailable.",
                message_code="ipg_encryption_unavailable",
                loc=["config"],
            )
        gateway = await self.gateways.create(
            GatewayModel(
                kind=data.kind,
                title=data.title,
                icon_url=str(data.icon_url) if data.icon_url else None,
                is_active=data.is_active,
            )
        )
        await self.configs.create(ConfigModel(key=gateway.kind, config=config))
        return gateway
