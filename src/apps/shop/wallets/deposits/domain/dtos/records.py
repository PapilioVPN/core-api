"""Validate the amount and selected method of a wallet top-up."""

from typing import Annotated, Literal

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType, RialType
from pydantic import Field

Amount = Annotated[RialType, Field(gt=0, strict=True)]


class CardDeposit(BaseDTO):
    amount: Amount
    method: Literal["card_to_card"]


class PlisioDeposit(BaseDTO):
    amount: Amount
    method: Literal["plisio"]
    gateway_id: IdType


DepositCreate = Annotated[
    CardDeposit | PlisioDeposit, Field(discriminator="method")
]
