"""Expose bank time, intake time and authenticated provenance."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import TransferSource


class TransferOutput(BaseOutput):
    id: int
    amount: int
    card_id: int | None
    transferred_at: datetime | None
    created_at: datetime
    source: TransferSource
    source_id: int
