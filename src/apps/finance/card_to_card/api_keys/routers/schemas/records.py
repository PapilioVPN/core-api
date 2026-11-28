"""Panel metadata and one-time disclosure for issued API keys."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput
from pydantic import Field


class APIKeyOutput(BaseOutput):
    id: int
    title: str
    prefix: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class APIKeyIssuedOutput(BaseOutput):
    api_key: APIKeyOutput
    key: str = Field(repr=False)
