"""Manual review contract for administrator entrypoints."""

from typing import Protocol

from ...domain.dtos.review import ReceiptReview
from ...domain.models.records import ReceiptModel


class IReceiptReviewCommand(Protocol):
    async def review(
        self, id: int, data: ReceiptReview, *, actor_id: int
    ) -> ReceiptModel: ...
