"""Validate bank deposit reports and panel filters."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, PageType, PerPageType, RialType
from pydantic import AwareDatetime, Field


class DepositCreate(BaseDTO):
    amount: Annotated[RialType, Field(gt=0, strict=True)]
    paid_at: AwareDatetime | None = None


class DepositSearch(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    amount: RialType | None = None
    payment_id: IdType | None = None
    matched: bool | None = None
