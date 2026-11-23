"""Native inputs for fixed volumes and custom volume ranges."""

from typing import Annotated, Literal, Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import BigIntType, PageType, PerPageType
from pydantic import Field, model_validator

from src.apps.shop.volumes.domain.dtos.validators.ranges import check_range
from src.apps.shop.volumes.domain.enums.records import VolumeMode

ByteCount = Annotated[BigIntType, Field(gt=0, strict=True)]


class FixedVolume(BaseDTO):
    mode: Literal[VolumeMode.FIXED]
    size_bytes: ByteCount


class CustomVolume(BaseDTO):
    mode: Literal[VolumeMode.CUSTOM]
    min_bytes: ByteCount
    max_bytes: ByteCount
    step_bytes: ByteCount

    @model_validator(mode="after")
    def check_bounds(self) -> Self:
        check_range(self.min_bytes, self.max_bytes, self.step_bytes)
        return self


VolumeCreate = FixedVolume | CustomVolume


class VolumeList(BaseDTO):
    mode: VolumeMode | None = None
    size_bytes: Annotated[BigIntType, Field(gt=0)] | None = None
    page: PageType = 1
    per_page: PerPageType = 20
