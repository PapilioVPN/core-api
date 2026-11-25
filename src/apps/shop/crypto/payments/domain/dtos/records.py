"""Validate the frozen terms of a new crypto payment."""

from decimal import Decimal
from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, RialType
from pydantic import Field

from src.apps.shop.crypto.types import CurrencyCode


class CryptoPaymentCreate(BaseDTO):
    gateway_id: IdType
    amount: Annotated[RialType, Field(gt=0, strict=True)]
    price_amount: Annotated[Decimal, Field(gt=0, strict=True)]
    price_currency: CurrencyCode
    pay_currency: CurrencyCode | None = None
