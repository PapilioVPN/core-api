"""Prepare gateway connection settings before writing them."""

from papilio.core.config import CryptoConfig
from papilio.errors.exceptions import ValidationException
from papilio.security.crypto import encrypt
from pydantic import JsonValue

from ...domain.dtos.configs import ConfigWrite
from ...domain.errors import ConfigUnavailable
from ...domain.results.configs import GatewayConfigView
from ..interfaces.configs import IGatewayConfigService
from ..interfaces.services import ICryptoGatewayService


class GatewayConfigCommand:
    def __init__(
        self,
        gateways: ICryptoGatewayService,
        configs: IGatewayConfigService,
        crypto: CryptoConfig,
    ) -> None:
        """Bind gateway lookup, settings writes and the deployment key."""
        self.gateways = gateways
        self.configs = configs
        self.crypto = crypto

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
            raise ValidationException(
                message="Configuration does not match the gateway provider.",
                message_code="crypto_gateway_kind_mismatch",
                loc=["kind"],
                input=data.kind,
            )
        key = self.crypto.encryption_key
        if not key.strip() or key == "replace-with-private-encryption-key":
            raise ConfigUnavailable()
        config: dict[str, JsonValue] = {
            "api_url": data.api_url,
            "api_key": encrypt(data.api_key.get_secret_value(), key),
        }
        if data.kind == "nowpayments":
            config["ipn_secret"] = encrypt(
                data.ipn_secret.get_secret_value(), key
            )
        else:
            config["price_currency"] = data.price_currency
        record = await self.configs.save(id, config)
        return GatewayConfigView.from_record(record, gateway.kind)
