"""Validate the frozen terms of a new crypto payment."""

from decimal import Decimal
from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import RialType, SlugType
from pydantic import Field

CurrencyCode = Annotated[
    str, Field(max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
]


class CryptoPaymentCreate(BaseDTO):
    gateway: SlugType
    amount: Annotated[RialType, Field(gt=0, strict=True)]
    price_amount: Annotated[Decimal, Field(gt=0, strict=True)]
    price_currency: CurrencyCode
    pay_currency: CurrencyCode | None = None
