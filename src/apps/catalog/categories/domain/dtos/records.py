"""Category inputs for catalog administration."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    ContentType,
    IntType,
    MStrType,
    PageType,
    PerPageType,
    SlugType,
    ValueType,
)
from pydantic_core import MISSING


class CategoryCreate(BaseDTO):
    slug: SlugType
    title: MStrType
    description: ContentType | None = None
    priority: IntType = 0
    is_active: bool = True


class CategoryUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    description: ContentType | None = None
    priority: IntType | MISSING = MISSING
    is_active: bool | MISSING = MISSING


class CategoryList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    q: ValueType | None = None
    is_active: bool | None = None
