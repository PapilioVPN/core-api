"""Manage the connection settings of one gateway account."""

from papilio.core.config import CryptoConfig
from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.security.crypto import encrypt
from papilio.tools.checks import Checks
from pydantic import JsonValue

from ...domain.dtos.configs import ConfigWrite
from ...domain.errors import ConfigUnavailable
from ...domain.models.configs import GatewayConfigModel
from ...domain.results.configs import GatewayConfigView
from ...infra.pg.repositories.configs import GatewayConfigRepository
from ..decorators.configs import forget_cache
from ..interfaces.cache import IGatewayConfigCache
from ..interfaces.services import ICryptoGatewayService


def _view(record: GatewayConfigModel, kind: str) -> GatewayConfigView:
    """Return connection metadata without including encrypted values."""
    api_url = record.config.get("api_url")
    if not isinstance(api_url, str):
        raise ConfigUnavailable()
    return GatewayConfigView(
        gateway_id=record.gateway_id,
        kind=kind,
        api_url=api_url,
        has_api_key=bool(record.config.get("api_key")),
        has_ipn_secret=bool(record.config.get("ipn_secret")),
    )


class GatewayConfigService(Checks[GatewayConfigModel]):
    entity = "GatewayConfig"

    def __init__(
        self,
        repo: GatewayConfigRepository,
        gateways: ICryptoGatewayService,
        crypto: CryptoConfig,
        cache: IGatewayConfigCache,
    ) -> None:
        """Bind account lookup, encrypted storage and panel cache eviction."""
        self.repo = repo
        self.gateways = gateways
        self.crypto = crypto
        self.cache = cache

    @transactional
    async def get(self, id: int) -> GatewayConfigView:
        """Read the saved settings without decrypting credentials.

        Args:
            id: Owning gateway account identity.

        Returns:
            Connection metadata and credential-presence flags.

        Raises:
            NotFoundException: The account or its settings do not exist.
            ConfigUnavailable: The stored connection metadata is invalid.
        """
        gateway = await self.gateways.get_by_id(id)
        record = await self.repo.get(id)
        settings = self._check_for_existence("gateway_id", id, record)
        return _view(settings, gateway.kind)

    @forget_cache.one
    @transactional
    async def save(self, id: int, data: ConfigWrite) -> GatewayConfigView:
        """Replace one account's connection settings.

        Args:
            id: Owning gateway account identity.
            data: Typed complete settings for that provider.

        Returns:
            The persisted credential-free projection.

        Raises:
            NotFoundException: The account does not exist.
            ConflictException: The input targets a different provider.
            ConfigUnavailable: A private deployment key is not configured.
        """
        gateway = await self.gateways.get_by_id(id)
        if gateway.kind != data.kind:
            raise ConflictException(
                message="Configuration does not match the gateway provider.",
                message_code="crypto_gateway_kind_mismatch",
                unique_dict={"gateway_id": id},
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
        record = await self.repo.save(
            GatewayConfigModel(gateway_id=id, config=config)
        )
        return _view(record, gateway.kind)
