"""Resolve the catalog's reusable volume and duration definitions."""

from src.apps.shop.products.durations.app.interfaces.services import (
    IDurationService,
)
from src.apps.shop.products.volumes.app.interfaces.services import (
    IVolumeService,
)

from ...domain.dtos.records import DurationRef, VolumeRef


class CatalogTermsService:
    def __init__(
        self, volumes: IVolumeService, durations: IDurationService
    ) -> None:
        """Bind the two owners of sale terms."""
        self.volumes = volumes
        self.durations = durations

    async def volume_id(self, data: VolumeRef) -> int | None:
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

    async def duration_id(self, data: DurationRef) -> int | None:
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
