"""Validate gateway account changes and filters."""

from typing import Literal

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    MediaUrlType,
    MStrType,
    PageType,
    PerPageType,
    ValueType,
)
from pydantic_core import MISSING

type GatewayKind = Literal["nowpayments", "plisio"]


class GatewayCreate(BaseDTO):
    kind: GatewayKind
    title: MStrType
    icon_url: MediaUrlType | None = None
    is_active: bool = False


class GatewayUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    icon_url: MediaUrlType | None | MISSING = MISSING
    is_active: bool | MISSING = MISSING


class GatewayList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    kind: GatewayKind | None = None
    is_active: bool | None = None
