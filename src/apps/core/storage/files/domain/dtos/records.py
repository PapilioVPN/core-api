"""Logical file selections; business owners retain access and upload policy."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    IdType,
    ListIdType,
    PageType,
    PerPageType,
    ValueType,
)


class FileBatchRead(BaseDTO):
    ids: ListIdType


class FileList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    content_id: IdType | None = None
    original_name: ValueType | None = None
    mime_type: ValueType | None = None
