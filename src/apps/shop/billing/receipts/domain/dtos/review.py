"""Manual decisions submitted for a bank receipt."""

from typing import Annotated, Literal, Self

from papilio.errors.exceptions import ValidationException
from papilio.schemas.inputs import BaseDTO
from pydantic import StringConstraints, model_validator

from ..enums.records import ReceiptStatus


class ReceiptReview(BaseDTO):
    status: Literal[ReceiptStatus.APPROVED, ReceiptStatus.REJECTED]
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
        """Allow an explanation on a rejection."""
        if self.status == ReceiptStatus.APPROVED and self.reason is not None:
            raise ValidationException(
                message="Only a rejected receipt can have a reason",
                message_code="invalid_receipt_rejection_reason",
                loc=["reason"],
            )
        return self
