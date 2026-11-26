"""Prepare gateway connection settings before writing them."""

from ...domain.dtos.configs import ConfigWrite
from ...domain.errors import GatewayKindMismatch
from ...domain.results.configs import GatewayConfigView
from ..interfaces.configs import IGatewayConfigService
from ..interfaces.services import ICryptoGatewayService


class GatewayConfigCommand:
    def __init__(
        self,
        gateways: ICryptoGatewayService,
        configs: IGatewayConfigService,
    ) -> None:
        """Bind gateway lookup and the settings writer."""
        self.gateways = gateways
        self.configs = configs

    async def save(self, id: int, data: ConfigWrite) -> GatewayConfigView:
        """Replace one account's connection settings.

        Args:
            id: Owning gateway account identity.
            data: Typed complete settings for that provider.

        Returns:
            The persisted credential-free projection.

        Raises:
            NotFoundException: The account does not exist.
            ValidationException: The input targets a different provider.
            ConfigUnavailable: A private deployment key is not configured.
        """
        gateway = await self.gateways.get_by_id(id)
        if gateway.kind != data.kind:
            raise GatewayKindMismatch(data.kind)
        record = await self.configs.save(id, data)
        return GatewayConfigView.from_record(record, gateway.kind)
