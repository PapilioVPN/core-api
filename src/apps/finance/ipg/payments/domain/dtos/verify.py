"""Validated scheduling limits for one IPG reconciliation pass."""

from papilio.schemas.inputs import BaseDTO
from pydantic import Field


class VerifyPolicy(BaseDTO):
    limit: int = Field(ge=1, le=100)
    parallel: int = Field(ge=1, le=16)
    retry_seconds: int = Field(ge=60, le=3600)
    window_minutes: int = Field(ge=1, le=10080)
