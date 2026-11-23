"""Validated inputs for managing and listing shop services."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    ContentType,
    IntType,
    MStrType,
    PageType,
    PerPageType,
    ValueType,
)
from pydantic_core import MISSING


class ServiceCreate(BaseDTO):
    title: MStrType
    description: ContentType | None = None
    is_active: bool = True
    priority: IntType = 0


class ServiceUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    description: ContentType | None = None
    is_active: bool | MISSING = MISSING
    priority: IntType | MISSING = MISSING


class ServiceList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    is_active: bool | None = None
