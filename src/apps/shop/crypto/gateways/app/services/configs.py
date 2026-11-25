"""Replace or read encrypted gateway configuration on its parent record."""

from papilio.core.config import CryptoConfig
from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.security.crypto import decrypt, encrypt
from papilio.tools.checks import Checks
from pydantic import JsonValue, SecretStr, ValidationError

from ...domain.dtos.configs import (
    ConfigWrite,
    NowPaymentsConfig,
    config_adapter,
)
from ...domain.errors import ConfigUnavailable
from ...domain.models.records import (
    CryptoGatewayConfigModel,
    CryptoGatewayModel,
)
from ...domain.results.configs import GatewayConfigView
from ...infra.pg.repositories.configs import CryptoGatewayConfigRepository
from ..decorators.configs import forget_cache
from ..interfaces.cache import IGatewayConfigCache
from ..interfaces.services import ICryptoGatewayService


def _parse(kind: str | None, record: CryptoGatewayConfigModel) -> ConfigWrite:
    """Validate stored data using the kind on the parent gateway."""
    try:
        config = config_adapter.validate_python(
            {**record.config, "kind": kind}
        )
    except ValidationError:
        raise ConfigUnavailable() from None
    return config


class CryptoGatewayConfigService(Checks[CryptoGatewayConfigModel]):
    entity = "CryptoGatewayConfig"

    def __init__(
        self,
        repo: CryptoGatewayConfigRepository,
        gateways: ICryptoGatewayService,
        crypto: CryptoConfig,
        cache: IGatewayConfigCache,
    ) -> None:
        """Bind encrypted storage and its owning gateway on one request."""
        self.repo = repo
        self.gateways = gateways
        self.crypto = crypto
        self.cache = cache

    def _key(self) -> str:
        """Read the deployment key used for gateway credentials."""
        key = self.crypto.encryption_key
        if not key.strip() or key == "replace-with-private-encryption-key":
            raise ConfigUnavailable()
        return key

    @transactional
    async def get(self, id: int) -> GatewayConfigView:
        """Read the panel projection without decrypting credentials.

        Args:
            id: Stored gateway identity.

        Returns:
            Connection settings and key presence, with no credentials.

        Raises:
            NotFoundException: The parent or its configuration is missing.
            ConfigUnavailable: The stored structure is not usable.
        """
        gateway = await self.gateways.get_by_id(id)
        record = await self.repo.find_by_gateway_id(id)
        record = self._check_for_existence("gateway_id", id, record)
        config = _parse(gateway.kind, record)
        return GatewayConfigView.from_config(id, config)

    @forget_cache.one
    @transactional
    async def save(self, id: int, data: ConfigWrite) -> GatewayConfigView:
        """Replace one gateway configuration and encrypt its supplied keys.

        Args:
            id: Stored gateway identity.
            data: Validated full configuration for the parent kind.

        Returns:
            Safe projection of the newly stored configuration.

        Raises:
            ConflictException: The input kind does not match the gateway.
            ConfigUnavailable: A deployment encryption key is not set.
        """
        gateway = await self.gateways.get_by_id(id)
        if gateway.kind != data.kind:
            raise ConflictException(
                message="The configuration kind does not match this gateway.",
                message_code="crypto_gateway_kind_mismatch",
                unique_dict={"id": id},
            )
        key = self._key()
        config: dict[str, JsonValue] = data.model_dump(
            mode="json", exclude={"kind", "api_key", "ipn_secret"}
        )
        config["api_key"] = encrypt(data.api_key.get_secret_value(), key)
        if isinstance(data, NowPaymentsConfig):
            config["ipn_secret"] = encrypt(
                data.ipn_secret.get_secret_value(), key
            )
        record = await self.repo.save(
            CryptoGatewayConfigModel(gateway_id=id, config=config)
        )
        return GatewayConfigView.from_config(id, _parse(gateway.kind, record))

    async def connection(self, gateway: CryptoGatewayModel) -> ConfigWrite:
        """Resolve current private connection settings from PostgreSQL.

        Args:
            gateway: Authoritative account already read by the payment command.

        Returns:
            Typed provider settings, materialized before outbound I/O.

        Raises:
            ConfigUnavailable: The config or its encrypted keys are unusable.
        """
        record = await self.repo.find_by_gateway_id(gateway.id)
        if record is None:
            raise ConfigUnavailable()
        stored = _parse(gateway.kind, record)
        key = self._key()
        try:
            secrets = {
                "api_key": SecretStr(
                    decrypt(stored.api_key.get_secret_value(), key)
                )
            }
            if isinstance(stored, NowPaymentsConfig):
                secrets["ipn_secret"] = SecretStr(
                    decrypt(stored.ipn_secret.get_secret_value(), key)
                )
        except ValueError:
            raise ConfigUnavailable() from None
        return stored.model_copy(update=secrets)
