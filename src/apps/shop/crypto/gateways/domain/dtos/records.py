"""Gateway sales settings and panel filters."""

from decimal import Decimal
from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    MediaUrlType,
    MStrType,
    PageType,
    PerPageType,
    SlugType,
)
from pydantic import Field
from pydantic_core import MISSING

from src.apps.shop.crypto.types import CurrencyCode

RialRate = Annotated[Decimal, Field(gt=0, max_digits=24, decimal_places=8)]


class GatewayCreate(BaseDTO):
    key: SlugType
    title: MStrType
    icon_url: MediaUrlType | None = None
    kind: SlugType
    price_currency: CurrencyCode
    pay_currency: CurrencyCode | None = None
    rial_rate: RialRate
    is_active: bool = False


class GatewayUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    icon_url: MediaUrlType | None | MISSING = MISSING
    price_currency: CurrencyCode | MISSING = MISSING
    pay_currency: CurrencyCode | None | MISSING = MISSING
    rial_rate: RialRate | MISSING = MISSING
    is_active: bool | MISSING = MISSING


class GatewayList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: MStrType | None = None
    kind: SlugType | None = None
    is_active: bool | None = None
