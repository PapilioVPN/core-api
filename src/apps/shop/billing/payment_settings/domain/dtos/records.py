"""Validate the automatic payment settings submitted by the panel."""

from typing import Annotated

from papilio.schemas.inputs import BaseDTO
from pydantic import Field, StrictBool

Digits = Annotated[int, Field(strict=True, ge=3, le=5)]


class PaymentSettingsWrite(BaseDTO):
    auto_confirm: StrictBool
    digits: Digits
    window_hours: Annotated[int, Field(strict=True, ge=1, le=32_767)] = 24
