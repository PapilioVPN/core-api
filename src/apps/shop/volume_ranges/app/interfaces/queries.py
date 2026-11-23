"""Customer-facing range reads and quote calculation."""

from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.volume_ranges.domain.dtos.quote import QuoteInput
from src.apps.shop.volume_ranges.domain.models.records import VolumeRangeModel
from src.apps.shop.volume_ranges.domain.results.quote import RangeQuote


class IPublicRangeQuery(Protocol):
    async def list(
        self, service_id: int, *, page: int, per_page: int
    ) -> PagedType[VolumeRangeModel]: ...


class IQuoteQuery(Protocol):
    async def quote(self, service_id: int, data: QuoteInput) -> RangeQuote: ...
