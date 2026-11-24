"""Coordinate range configuration and its owning service."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.products.services.app.interfaces.services import (
    IShopService,
)
from src.apps.shop.products.volume_ranges.app.interfaces.services import (
    IVolumeRangeService,
)
from src.apps.shop.products.volume_ranges.app.validators.price import (
    validate_price,
)
from src.apps.shop.products.volume_ranges.domain.dtos.records import RangeWrite
from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)


class RangeCommand:
    def __init__(
        self, services: IShopService, ranges: IVolumeRangeService
    ) -> None:
        """Bind the service reader and range writer."""
        self.services = services
        self.ranges = ranges

    @transactional
    async def create(
        self, service_id: int, data: RangeWrite
    ) -> VolumeRangeModel:
        """Check the owning service and store a valid sale rule.

        Args:
            service_id: Required service identity.
            data: Validated range definition.

        Returns:
            The stored range.

        Raises:
            NotFoundException: The owning service is absent.
            ConflictException: A range under that service overlaps.
        """
        validate_price(data.min_bytes, data.max_bytes, data.price_per_gib)
        await self.services.get_by_id(service_id)
        row = await self.ranges.create(
            VolumeRangeModel(
                service_id=service_id,
                min_bytes=data.min_bytes,
                max_bytes=data.max_bytes,
                step_bytes=data.step_bytes,
                price_per_gib=data.price_per_gib,
                min_days=data.min_days,
                max_days=data.max_days,
                step_days=data.step_days,
                is_active=data.is_active,
            )
        )
        return row

    async def replace(
        self, service_id: int, id: int, data: RangeWrite
    ) -> VolumeRangeModel:
        """Replace an existing rule while preserving its identity and owner.

        Args:
            service_id: Required service identity.
            id: Stored range identity.
            data: Complete replacement definition.

        Returns:
            The updated range.
        """
        validate_price(data.min_bytes, data.max_bytes, data.price_per_gib)
        row = await self.ranges.replace(service_id, id, data)
        return row
