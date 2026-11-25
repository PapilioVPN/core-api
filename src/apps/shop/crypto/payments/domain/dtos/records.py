"""Validate the original rial amount and chosen gateway."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, RialType
from pydantic import Field


class PaymentCreate(BaseDTO):
    gateway_id: IdType
    amount: Annotated[RialType, Field(gt=0, strict=True)]
