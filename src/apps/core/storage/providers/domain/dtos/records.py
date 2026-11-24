"""Connection metadata inputs; configuration and activation are separate."""

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
from pydantic import Field
from pydantic_core import MISSING


class StorageProviderCreate(BaseDTO):
    """Create inactive metadata with a user-defined immutable key."""

    key: SlugType
    title: MStrType
    description: ContentType | None = None


class StorageProviderUpdate(BaseDTO):
    title: MStrType | MISSING = MISSING
    description: ContentType | None = None


class StorageProviderActivityUpdate(BaseDTO):
    is_active: bool


class StorageProviderList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    title: ValueType | None = None
    is_active: bool | None = None


class StorageProviderBatchRead(BaseDTO):
    ids: ListIdType


class StorageProviderKeyBatchRead(BaseDTO):
    keys: list[SlugType] = Field(min_length=1, max_length=100)
