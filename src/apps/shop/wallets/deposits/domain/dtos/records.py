"""Validate the amount of a wallet top-up."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import RialType
from pydantic import Field


class DepositCreate(BaseDTO):
    amount: Annotated[RialType, Field(gt=0, strict=True)]
