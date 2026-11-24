"""Receipt registration using an uploaded image address."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import RialType
from pydantic import AwareDatetime, Field


class ReceiptCreate(BaseDTO):
    image_url: Annotated[
        str,
        Field(
            max_length=255,
            pattern=r"^/(?:[A-Za-z0-9_-]+/)*admin/receipts/images/"
            r"(?:jpeg|png|webp)/[a-f0-9]{64}$",
        ),
    ]
    amount: Annotated[RialType, Field(gt=0, strict=True)] | None = None
    paid_at: AwareDatetime | None = None
