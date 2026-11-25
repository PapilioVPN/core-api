"""Validate the requested wallet top-up amount."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import RialType
from pydantic import Field


class TopupInput(BaseDTO):
    amount: Annotated[RialType, Field(gt=0, strict=True)]
