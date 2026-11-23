"""Validated customer group settings and list filters."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    IntType,
    MStrType,
    PageType,
    PerPageType,
    RialType,
    SlugType,
    ValueType,
)
from pydantic_core import MISSING


class GroupCreate(BaseDTO):
    key: SlugType
    title: MStrType
    min_spend: RialType
    is_active: bool = True
    priority: IntType = 0


class GroupUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    min_spend: RialType | MISSING = MISSING
    is_active: bool | MISSING = MISSING
    priority: IntType | MISSING = MISSING


class GroupList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    is_active: bool | None = None
