"""Card prefix output with its owning bank identity."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class CardPrefixOutput(BaseOutput):
    id: int
    bank_id: int
    prefix: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
