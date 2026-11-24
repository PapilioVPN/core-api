"""File reference output and syntactically valid declared MIME input."""

from datetime import datetime
from typing import Annotated

from papilio.schemas.outputs import BaseOutput
from papilio.types.aliases import ValueType
from pydantic import Field

from src.apps.core.storage.files.domain.dtos.uploads import FileUpload


class FileUploadInput(FileUpload):
    mime_type: Annotated[
        ValueType,
        Field(pattern=r"^[A-Za-z0-9!#$&^_.+\-]+/[A-Za-z0-9!#$&^_.+\-]+$"),
    ]


class FileOutput(BaseOutput):
    id: int
    content_id: int
    original_name: str
    mime_type: str
    created_at: datetime
    updated_at: datetime
