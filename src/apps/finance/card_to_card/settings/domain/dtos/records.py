"""Validate complete and partial settings submitted by the Finance panel."""

from typing import Annotated, Self

from papilio.errors.exceptions import ValidationException
from papilio.schemas.inputs import BaseDTO
from papilio.types.constants import INT32_MAX
from pydantic import Field, StrictBool, model_validator
from pydantic_core import MISSING

Digits = Annotated[int, Field(strict=True, ge=3, le=5)]
WindowMinutes = Annotated[int, Field(strict=True, gt=0, le=INT32_MAX)]


def validate_window(auto_confirm: bool, window_minutes: int | None) -> None:
    """Require a matching window when auto confirmation is enabled."""
    if auto_confirm and window_minutes is None:
        raise ValidationException(
            message="Auto confirmation requires a matching window.",
            message_code="card_transfer_window_required",
            loc=["window_minutes"],
        )


class TransferSettingsWrite(BaseDTO):
    auto_confirm: StrictBool
    digits: Digits
    window_minutes: WindowMinutes | None

    @model_validator(mode="after")
    def require_window(self) -> Self:
        validate_window(self.auto_confirm, self.window_minutes)
        return self


class TransferSettingsUpdate(BaseDTO):
    auto_confirm: StrictBool | MISSING = MISSING
    digits: Digits | MISSING = MISSING
    window_minutes: WindowMinutes | None | MISSING = MISSING
