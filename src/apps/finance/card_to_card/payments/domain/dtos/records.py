"""Validate card payment creation and panel filters."""

from typing import Annotated, Self

from papilio.errors.exceptions import ValidationException
from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import (
    IdType,
    MediaUrlType,
    PageType,
    PerPageType,
    RialType,
)
from pydantic import AwareDatetime, Field, model_validator

from ..enums.records import PaymentMode, PaymentStatus


class CardPaymentCreate(BaseDTO):
    card_id: Annotated[IdType, Field(strict=True)]
    amount: Annotated[RialType, Field(gt=0, strict=True)]
    receipt_url: MediaUrlType
    description: Annotated[str, Field(max_length=500)] | None = None


class AutoPaymentCreate(BaseDTO):
    card_id: Annotated[IdType, Field(strict=True)]
    amount: Annotated[RialType, Field(gt=0, strict=True)]


class CardPaymentList(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    card_id: IdType | None = None
    status: PaymentStatus | None = None
    mode: PaymentMode | None = None
    code: Annotated[str, Field(pattern=r"^[0-9]{3,5}$")] | None = None
    amount: Annotated[RialType, Field(gt=0)] | None = None
    payable_amount: Annotated[RialType, Field(gt=0)] | None = None
    transfer_id: IdType | None = None
    expired: bool | None = None
    since: AwareDatetime | None = None
    until: AwareDatetime | None = None

    @model_validator(mode="after")
    def check_range(self) -> Self:
        """Require the exclusive upper bound to follow the lower bound."""
        if (
            self.since is not None
            and self.until is not None
            and self.until <= self.since
        ):
            raise ValidationException(
                message="Until must be after since",
                message_code="invalid_card_payment_range",
                loc=["until"],
            )
        return self
