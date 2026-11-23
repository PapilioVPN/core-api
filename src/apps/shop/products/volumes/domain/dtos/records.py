"""Native inputs for reusable fixed volumes."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import BigIntType, PageType, PerPageType
from pydantic import Field

ByteCount = Annotated[BigIntType, Field(gt=0, strict=True)]


class VolumeCreate(BaseDTO):
    size_bytes: ByteCount


class VolumeList(BaseDTO):
    size_bytes: Annotated[BigIntType, Field(gt=0)] | None = None
    page: PageType = 1
    per_page: PerPageType = 20
