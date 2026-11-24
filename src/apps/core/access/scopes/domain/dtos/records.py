"""Validated scope creation, partial updates and bounded listing inputs."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    ContentType,
    MStrType,
    PageType,
    PerPageType,
    SlugType,
    ValueType,
)
from pydantic_core import MISSING


class ScopeCreate(BaseDTO):
    key: SlugType
    title: MStrType
    description: ContentType | None = None
    is_active: bool = True


class ScopeUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    description: ContentType | None = None
    is_active: bool | MISSING = MISSING


class ScopeList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    title: ValueType | None = None
    is_active: bool | None = None
