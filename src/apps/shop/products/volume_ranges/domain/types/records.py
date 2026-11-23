"""Units used by custom volume sales."""

from typing import Annotated

from papilio.types.aliases import BigIntType, IntType, RialType
from pydantic import Field

GIB = 1024**3
MIN_PRICE = 10_000

VolumeType = Annotated[BigIntType, Field(gt=0, multiple_of=GIB)]
VolumeInput = Annotated[VolumeType, Field(strict=True)]
DayType = Annotated[IntType, Field(gt=0)]
RateType = Annotated[RialType, Field(gt=0, strict=True)]
