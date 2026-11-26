"""Validate top-up amounts and panel filters."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType, RialType
from pydantic import Field


class DepositCreate(BaseDTO):
    amount: Annotated[RialType, Field(gt=0, strict=True)]


class DepositSearch(BaseDTO):
    page: PageType = 1
    per_page: PerPageType = 20
    amount: Annotated[RialType, Field(gt=0)] | None = None
