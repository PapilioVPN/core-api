"""Validate the amount and selected method of a wallet top-up."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import RialType
from pydantic import Field


class DepositCreate(BaseDTO):
    amount: Annotated[RialType, Field(gt=0, strict=True)]
    method: Literal["card_to_card"]
