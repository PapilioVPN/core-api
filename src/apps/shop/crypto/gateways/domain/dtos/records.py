"""Validate gateway account changes and filters."""

from typing import Annotated, Literal, Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    MediaUrlType,
    MStrType,
    PageType,
    PerPageType,
    RialType,
    ValueType,
)
from pydantic import Field, model_validator
from pydantic_core import MISSING

from .validators.limits import validate_limits

type GatewayKind = Literal["nowpayments", "plisio"]
GatewayAmount = Annotated[RialType, Field(gt=0, strict=True)]


class GatewayCreate(BaseDTO):
    kind: GatewayKind
    title: MStrType
    icon_url: MediaUrlType | None = None
    is_active: bool = False
    min_amount: GatewayAmount | None = None
    max_amount: GatewayAmount | None = None

    @model_validator(mode="after")
    def check_limits(self) -> Self:
        validate_limits(self.min_amount, self.max_amount)
        return self


class GatewayUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    icon_url: MediaUrlType | None | MISSING = MISSING
    is_active: bool | MISSING = MISSING
    min_amount: GatewayAmount | None | MISSING = MISSING
    max_amount: GatewayAmount | None | MISSING = MISSING

    @model_validator(mode="after")
    def check_limits(self) -> Self:
        if self.min_amount is not MISSING and self.max_amount is not MISSING:
            validate_limits(self.min_amount, self.max_amount)
        return self


class GatewayList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    kind: GatewayKind | None = None
    is_active: bool | None = None
