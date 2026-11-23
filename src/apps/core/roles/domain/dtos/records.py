"""Native role inputs and bounded read selections."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    ContentType,
    ListIdType,
    MStrType,
    PageType,
    PerPageType,
    SlugType,
    ValueType,
)
from pydantic_core import MISSING


class RoleCreate(BaseDTO):
    key: SlugType
    title: MStrType
    description: ContentType | None = None
    is_active: bool = True


class RoleUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    description: ContentType | None = None
    is_active: bool | MISSING = MISSING


class RoleList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    title: ValueType | None = None
    is_active: bool | None = None


class RoleBatchRead(BaseDTO):
    ids: ListIdType
