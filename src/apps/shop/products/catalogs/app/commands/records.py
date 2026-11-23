"""Coordinate catalog writes that resolve service and sale definitions."""

from papilio.infra.db.tools.decorators import transactional
from pydantic_core import MISSING

from src.apps.shop.products.catalogs.app.interfaces.services import (
    ICatalogCRUD,
)
from src.apps.shop.products.catalogs.domain.dtos.records import (
    CatalogCreate,
    CatalogPatch,
    CatalogUpdate,
    DurationRef,
    VolumeRef,
)
from src.apps.shop.products.catalogs.domain.models.records import CatalogModel
from src.apps.shop.products.durations.app.interfaces.services import (
    IDurationCRUD,
)
from src.apps.shop.products.services.app.interfaces.services import (
    IServiceCRUD,
)
from src.apps.shop.products.volumes.app.interfaces.services import IVolumeCRUD


class CatalogCommand:
    def __init__(
        self,
        catalogs: ICatalogCRUD,
        services: IServiceCRUD,
        volumes: IVolumeCRUD,
        durations: IDurationCRUD,
    ) -> None:
        """Bind the record service and the owners of its sale definitions.

        Args:
            catalogs: Catalog record operations on the request UoW.
            services: Authoritative service definitions.
            volumes: Reusable fixed volumes on that same UoW.
            durations: Reusable durations on that same UoW.

        Returns:
            None.
        """
        self.catalogs = catalogs
        self.services = services
        self.volumes = volumes
        self.durations = durations

    async def _volume_id(self, data: VolumeRef) -> int | None:
        """Resolve the catalog's optional volume.

        Args:
            data: A stored ID, fixed byte count input or None for unlimited.

        Returns:
            The stored ID or None for unlimited volume.
        """
        match data:
            case None:
                id = None
            case int():
                volume = await self.volumes.get_by_id(data)
                id = volume.id
            case _:
                volume = await self.volumes.create(data)
                id = volume.id
        return id

    async def _duration_id(self, data: DurationRef) -> int | None:
        """Resolve the catalog's optional duration.

        Args:
            data: A stored ID, fixed duration input or None for no expiry.

        Returns:
            The stored ID or None for no expiry.
        """
        match data:
            case None:
                id = None
            case int():
                duration = await self.durations.get_by_id(data)
                id = duration.id
            case _:
                duration = await self.durations.create(data)
                id = duration.id
        return id

    @transactional
    async def create(self, data: CatalogCreate) -> CatalogModel:
        """Register a catalog and resolve its terms in one transaction.

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
        catalog = await self.catalogs.create(
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

    @transactional
    async def update(self, id: int, data: CatalogUpdate) -> CatalogModel:
        """Apply a profile patch and its resolved terms atomically.

        Args:
            id: Stored catalog identity.
            data: Original patch. Null clears a supplied term reference.

        Returns:
            Updated catalog, preserving every omitted field.

        Raises:
            NotFoundException: The catalog or a selected term is absent.
            ValidationException: The patch has no recognized changes.
        """
        volume_id = MISSING
        if data.volume is not MISSING:
            volume_id = await self._volume_id(data.volume)
        duration_id = MISSING
        if data.duration is not MISSING:
            duration_id = await self._duration_id(data.duration)
        patch = CatalogPatch.model_construct(
            title=data.title,
            price=data.price,
            priority=data.priority,
            status=data.status,
            volume_id=volume_id,
            duration_id=duration_id,
        )
        catalog = await self.catalogs.update(id, patch)
        return catalog
