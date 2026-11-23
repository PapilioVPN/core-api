"""Create and update catalogs with transactionally resolved terms."""

from papilio.infra.db.tools.decorators import transactional
from papilio.infra.db.transaction import transaction
from papilio.tools.checks import IDChecks
from pydantic_core import MISSING

from src.apps.shop.catalogs.domain.dtos.records import (
    CatalogCreate,
    CatalogUpdate,
    DurationRef,
    VolumeRef,
)
from src.apps.shop.catalogs.domain.models.records import CatalogModel
from src.apps.shop.catalogs.infra.pg.repositories.records import (
    CatalogRepository,
)
from src.apps.shop.catalogs.infra.redis.repositories.details import (
    CatalogCache,
)
from src.apps.shop.durations.app.interfaces.services import IDurations
from src.apps.shop.services.app.interfaces.services import IServices
from src.apps.shop.volumes.app.interfaces.services import IVolumes


class CatalogCommand(IDChecks[CatalogModel]):
    entity = "Catalog"

    def __init__(
        self,
        repo: CatalogRepository,
        services: IServices,
        volumes: IVolumes,
        durations: IDurations,
        cache: CatalogCache,
    ) -> None:
        """Bind catalog storage, owning references and its detail cache."""
        self.repo = repo
        self.services = services
        self.volumes = volumes
        self.durations = durations
        self.cache = cache

    async def _volume_id(self, data: VolumeRef) -> int | None:
        if data is None:
            return None
        if isinstance(data, int):
            volume = await self.volumes.get_by_id(data)
        else:
            volume = await self.volumes.create(data)
        return volume.id

    async def _duration_id(self, data: DurationRef) -> int | None:
        if data is None:
            return None
        if isinstance(data, int):
            duration = await self.durations.get_by_id(data)
        else:
            duration = await self.durations.create(data)
        return duration.id

    @transactional
    async def create(self, data: CatalogCreate) -> CatalogModel:
        """Register a catalog and resolve its terms in the same transaction.

        Args:
            data: Validated service, fixed rial price, and optional terms.

        Returns:
            The stored catalog with the resolved term identities.

        Raises:
            NotFoundException: A selected service or term is absent.
        """
        await self.services.get_by_id(data.service_id)
        volume_id = await self._volume_id(data.volume)
        duration_id = await self._duration_id(data.duration)
        catalog = await self.repo.create(
            CatalogModel(
                service_id=data.service_id,
                title=data.title,
                price=data.price,
                priority=data.priority,
                status=data.status,
                volume_id=volume_id,
                duration_id=duration_id,
            )
        )
        return catalog

    async def update(self, id: int, data: CatalogUpdate) -> CatalogModel:
        """Change a catalog and invalidate its detail after the write.

        Args:
            id: Stored catalog identity.
            data: Validated patch. Explicit null removes a term reference.

        Returns:
            The updated catalog with the supplied changes applied.

        Raises:
            NotFoundException: The catalog or a selected term is absent.
            ValidationException: The patch has no recognized changes.
        """
        changes = data.model_dump(
            exclude={"volume", "duration"}, exclude_unset=True
        )
        async with transaction():
            if data.volume is not MISSING:
                changes["volume_id"] = await self._volume_id(data.volume)
            if data.duration is not MISSING:
                changes["duration_id"] = await self._duration_id(data.duration)
            self._check_not_empty_dict(changes)
            catalog = await self.repo.update_by_id(id, changes)
            catalog = self._check_for_id_existence(id, catalog)
        await self.cache.forget(catalog.id)
        return catalog
