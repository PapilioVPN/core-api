"""Validated registration inputs supplied by the owning payment flow."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, RialType
from pydantic import Field

from ..enums.records import PaymentSource


class PaymentCreate(BaseDTO):
    customer_id: IdType
    source: PaymentSource
    source_id: IdType
    amount: Annotated[RialType, Field(gt=0, strict=True)]
