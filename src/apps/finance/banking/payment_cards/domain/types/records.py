"""A card number validated offline using its checksum."""

from typing import Annotated

from papilio.types.aliases import ContentType
from pydantic import AfterValidator, Field

from ..dtos.validators.number import validate_card_number

CardNumberType = Annotated[
    ContentType,
    Field(min_length=16, max_length=16, pattern=r"^[0-9]{16}$"),
    AfterValidator(validate_card_number),
]
