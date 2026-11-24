"""Validated manual payment decisions."""

from typing import Annotated, Literal, Self

from papilio.errors.exceptions import ValidationException
from papilio.schemas.inputs import BaseDTO
from pydantic import StringConstraints, model_validator

from ..enums.records import PaymentStatus


class PaymentReview(BaseDTO):
    status: Literal[PaymentStatus.CONFIRMED, PaymentStatus.REJECTED]
    reason: (
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True, min_length=1, max_length=500
            ),
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def check_reason(self) -> Self:
        """Allow a reason when rejecting a payment."""
        if self.status == PaymentStatus.CONFIRMED and self.reason is not None:
            raise ValidationException(
                message="Only a rejected payment can have a reason",
                message_code="invalid_payment_rejection_reason",
                loc=["reason"],
            )
        return self
