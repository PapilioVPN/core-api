"""Explicit administrator credential output at the HTTP boundary."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput
from pydantic import Field


class TokenPairOutput(BaseOutput):
    access_token: str = Field(repr=False)
    refresh_token: str = Field(repr=False)
    access_expires_at: datetime
    refresh_expires_at: datetime
