"""Filters for the administrator's payment list."""

from typing import Self

from papilio.errors.exceptions import ValidationException
from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType, RialType
from pydantic import AwareDatetime, model_validator

from ..enums.records import PaymentStatus


class PaymentSearch(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    status: PaymentStatus | None = None
    amount: RialType | None = None
    created_since: AwareDatetime | None = None
    created_until: AwareDatetime | None = None

    @model_validator(mode="after")
    def check_range(self) -> Self:
        """Require the exclusive upper bound to follow the lower bound."""
        since, until = self.created_since, self.created_until
        if since is not None and until is not None and until <= since:
            raise ValidationException(
                message="Created until must be after created since",
                message_code="invalid_payment_range",
                loc=["created_until"],
            )
        return self
