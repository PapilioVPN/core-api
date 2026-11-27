"""Prepare gateway connection settings before writing them."""

from papilio.errors.exceptions import ValidationException

from ...domain.dtos.configs import ConfigWrite
from ...domain.results.configs import ConfigFailure, GatewayConfigView
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

    async def save(
        self, id: int, data: ConfigWrite
    ) -> GatewayConfigView | ConfigFailure:
        """Replace one account's connection settings.

        Args:
            id: Owning gateway account identity.
            data: Typed complete settings for that provider.

        Returns:
            The persisted credential-free projection.

        Raises:
            NotFoundException: The account does not exist.
            ValidationException: The input targets a different provider.
        """
        gateway = await self.gateways.get_by_id(id)
        if gateway.kind != data.kind:
            raise ValidationException(
                message="Configuration does not match the gateway provider.",
                message_code="crypto_gateway_kind_mismatch",
                loc=["kind"],
                input=data.kind,
            )
        record = await self.configs.save(id, data)
        result = (
            record
            if isinstance(record, ConfigFailure)
            else GatewayConfigView.from_record(record, gateway.kind)
        )
        return result
