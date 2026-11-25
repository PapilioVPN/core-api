"""Manage the connection settings of one gateway account."""

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import Checks
from pydantic import JsonValue

from ...domain.models.configs import GatewayConfigModel
from ...domain.results.configs import GatewayConfigView
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
    ) -> None:
        """Bind account reads, settings storage and cache eviction."""
        self.repo = repo
        self.gateways = gateways
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
        return GatewayConfigView.from_record(settings, gateway.kind)

    @forget_cache.one
    @transactional
    async def save(
        self, id: int, config: dict[str, JsonValue]
    ) -> GatewayConfigModel:
        """Persist prepared settings and invalidate the cached panel view.

        Args:
            id: Owning gateway account identity.
            config: Settings containing encrypted credential values.

        Returns:
            The stored settings.
        """
        record = await self.repo.save(
            GatewayConfigModel(gateway_id=id, config=config)
        )
        return record
