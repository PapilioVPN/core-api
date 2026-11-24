"""Metadata for supported receipt image uploads."""

from typing import Annotated

from papilio.types.aliases import ValueType
from pydantic import Field

from src.apps.core.storage.files.domain.dtos.uploads import FileUpload


class ReceiptUpload(FileUpload):
    mime_type: Annotated[ValueType, Field(pattern=r"^image/(jpeg|png|webp)$")]
