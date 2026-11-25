"""Validate one scheduled payment batch."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from pydantic import Field


class PaymentRecheck(BaseDTO):
    limit: Annotated[int, Field(ge=1, le=25)]
    delay: Annotated[int, Field(ge=60)]
