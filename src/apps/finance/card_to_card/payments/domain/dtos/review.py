"""Accept a final decision and optional reason for rejection."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from pydantic import Field

from ..enums.records import PaymentStatus


class CardPaymentReview(BaseDTO):
    status: Literal[PaymentStatus.CONFIRMED, PaymentStatus.REJECTED]
    reason: Annotated[str, Field(max_length=500)] | None = None
