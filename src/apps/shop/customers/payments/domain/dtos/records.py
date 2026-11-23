"""Validated payment registration and review inputs."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, RialType
from pydantic import AwareDatetime, Field, StringConstraints

from ..enums.records import PaymentStatus


class PaymentCreate(BaseDTO):
    customer_id: IdType
    card_id: IdType
    amount: Annotated[RialType, Field(gt=0, strict=True)]
    reference: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=64),
    ]
    paid_at: AwareDatetime | None = None


class PaymentReview(BaseDTO):
    status: Literal[PaymentStatus.CONFIRMED, PaymentStatus.REJECTED]
