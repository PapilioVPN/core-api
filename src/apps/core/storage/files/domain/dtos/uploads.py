"""Logical metadata supplied by an upload's owning business capability."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import ContentType, ValueType
from pydantic import Field


class FileUpload(BaseDTO):
    original_name: Annotated[ContentType, Field(min_length=1)]
    mime_type: ValueType
