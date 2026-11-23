"""Receipt amount and supported image media types."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import RialType
from papilio.types.enums import MediaType
from pydantic import Field

ImageType = Literal[MediaType.JPEG, MediaType.PNG, MediaType.WEBP]


class ReceiptCreate(BaseDTO):
    amount: Annotated[RialType, Field(gt=0)]
