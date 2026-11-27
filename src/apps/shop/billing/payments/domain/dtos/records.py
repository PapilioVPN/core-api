"""Validate the external input for a new payment and its receipt."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import MediaUrlType, RialType
from pydantic import Field


class PaymentCreate(BaseDTO):
    amount: Annotated[RialType, Field(gt=0, strict=True)]
    image_url: MediaUrlType


class PaymentReceipt(BaseDTO):
    image_url: MediaUrlType
