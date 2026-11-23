"""Payment card fields available to authorized Shop operators."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class CardOutput(BaseOutput):
    id: int
    bank_id: int
    card_number: str
    holder_name: str
    is_active: bool
    allow_manual: bool
    allow_auto: bool
    created_at: datetime
    updated_at: datetime
