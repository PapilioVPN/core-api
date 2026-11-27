"""Manage the connection settings of one gateway account."""

from papilio.core.config import CryptoConfig
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import Checks

from ...domain.dtos.configs import ConfigWrite, PriceCurrency
from ...domain.models.configs import GatewayConfigModel
from ...domain.results.configs import (
    ConfigFailure,
    GatewayConfigView,
    plisio_currency,
)
from ...infra.crypto.codec import encode
from ...infra.pg.repositories.configs import GatewayConfigRepository
from ..decorators.configs import forget_cache
from ..interfaces.cache import IGatewayConfigCache
from ..interfaces.services import ICryptoGatewayService


class GatewayConfigService(Checks[GatewayConfigModel]):
    entity = "GatewayConfig"

    def __init__(
        self,
        repo: GatewayConfigRepository,
        gateways: ICryptoGatewayService,
        cache: IGatewayConfigCache,
        crypto: CryptoConfig,
    ) -> None:
        """Bind account reads, settings storage and cache eviction."""
        self.repo = repo
        self.gateways = gateways
        self.cache = cache
        self.crypto = crypto

    @transactional
    async def get(self, id: int) -> GatewayConfigView | ConfigFailure:
        """Read the saved settings without decrypting credentials.

        Args:
            id: Owning gateway account identity.

        Returns:
            Connection metadata and credential-presence flags.

        Raises:
            NotFoundException: The account or its settings do not exist.
        """
        gateway = await self.gateways.get_by_id(id)
        record = await self.find(id)
        settings = self._check_for_existence("gateway_id", id, record)
        return GatewayConfigView.from_record(settings, gateway.kind)

    async def find(self, id: int) -> GatewayConfigModel | None:
        """Read stored settings by gateway ID without decrypting them.

        Args:
            id: Owning gateway account identity.

        Returns:
            Encrypted settings or None if the account has no settings.
        """
        record = await self.repo.get(id)
        return record

    async def plisio_price(self, id: int) -> PriceCurrency | ConfigFailure:
        """Read authoritative pricing for a Plisio account.

        Args:
            id: Plisio gateway account identity.

        Returns:
            The saved currency, default IRR, or an invalid settings result.
        """
        record = await self.find(id)
        return plisio_currency(record)

    @forget_cache.one
    @transactional
    async def save(
        self, id: int, data: ConfigWrite
    ) -> GatewayConfigModel | ConfigFailure:
        """Persist prepared settings and invalidate the cached panel view.

        Args:
            id: Owning gateway account identity.
            data: Validated settings, with credentials to encrypt.

        Returns:
            The stored settings or an encryption failure.
        """
        config = encode(data, self.crypto.encryption_key)
        result: GatewayConfigModel | ConfigFailure = ConfigFailure.UNAVAILABLE
        if not isinstance(config, ConfigFailure):
            result = await self.repo.save(
                GatewayConfigModel(gateway_id=id, config=config)
            )
        return result
