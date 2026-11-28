"""Inputs for managing online payment gateway accounts."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import MStrType, PageType, PerPageType
from pydantic import HttpUrl, StrictBool
from pydantic_core import MISSING

from ..enums.records import GatewayKind
from .configs import GatewayConfig


class GatewayCreate(BaseDTO):
    kind: GatewayKind
    title: MStrType
    icon_url: HttpUrl | None = None
    is_active: StrictBool = False
    config: GatewayConfig


class GatewayUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    icon_url: HttpUrl | None | MISSING = MISSING
    is_active: StrictBool | MISSING = MISSING


class GatewayList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: MStrType | None = None
    kind: GatewayKind | None = None
    is_active: bool | None = None
