"""Bounds for one scheduled payment recheck."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from pydantic import Field


class PaymentRecheck(BaseDTO):
    limit: Annotated[int, Field(ge=1, le=100)]
    delay: Annotated[int, Field(ge=60)]
    concurrency: Annotated[int, Field(ge=1, le=8)]
