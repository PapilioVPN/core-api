"""Quote a customer selection using the current published range."""

from papilio.tools.checks import Checks

from src.apps.shop.volume_ranges.app.validators.price import price_for
from src.apps.shop.volume_ranges.app.validators.quote import validate_quote
from src.apps.shop.volume_ranges.domain.dtos.quote import QuoteInput
from src.apps.shop.volume_ranges.domain.models.records import VolumeRangeModel
from src.apps.shop.volume_ranges.domain.results.quote import RangeQuote
from src.apps.shop.volume_ranges.infra.pg.readers.quote import QuoteReader


class QuoteQuery(Checks[VolumeRangeModel]):
    entity = "VolumeRange"

    def __init__(self, reader: QuoteReader) -> None:
        """Bind the request's quote reader."""
        self.reader = reader

    async def quote(self, service_id: int, data: QuoteInput) -> RangeQuote:
        """Validate a selection and calculate its integer rial price.

        Args:
            service_id: Required owning service.
            data: Validated volume in bytes and optional days.

        Returns:
            The priced selection and the rule that supplied its rate.

        Raises:
            NotFoundException: No active range covers the requested volume.
            ValidationException: The volume step or duration is invalid.
        """
        rule = await self.reader.find(service_id, data.volume_bytes)
        rule = self._check_for_existence(
            "volume_bytes", data.volume_bytes, rule
        )
        validate_quote(rule, data)
        return RangeQuote(
            range_id=rule.id,
            volume_bytes=data.volume_bytes,
            days=data.days,
            price=price_for(data.volume_bytes, rule.price_per_gib),
        )
