"""Validate the initial amount and gateway page requested by the panel."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import PageType, PerPageType, RialType
from pydantic import Field


class DepositMethods(BaseDTO):
    amount: Annotated[RialType, Field(gt=0)]
    page: PageType = 1
    per_page: PerPageType = 20
