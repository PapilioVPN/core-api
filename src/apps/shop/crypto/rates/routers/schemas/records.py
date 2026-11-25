"""The rate and observation timestamp shown in the Shop panel."""

from datetime import datetime
from decimal import Decimal

from papilio.schemas.outputs import BaseOutput


class RateOutput(BaseOutput):
    currency: str
    rial_rate: Decimal
    source: str
    fetched_at: datetime
