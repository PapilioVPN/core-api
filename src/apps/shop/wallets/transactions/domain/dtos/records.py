"""Validate a wallet movement and its optional description."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import RialType
from pydantic import Field


class TransactionPost(BaseDTO):
    amount: Annotated[RialType, Field(gt=0, strict=True)]
    description: Annotated[str, Field(max_length=500)] | None = None
