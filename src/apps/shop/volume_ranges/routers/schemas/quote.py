"""The HTTP price of the selected volume and duration."""

from papilio.schemas.outputs import BaseOutput


class QuoteOutput(BaseOutput):
    range_id: int
    volume_bytes: int
    days: int | None
    price: int
