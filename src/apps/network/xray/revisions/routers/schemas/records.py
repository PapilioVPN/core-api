"""Credential-free metadata for the panel's stored revision catalog."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput
from pydantic import BaseModel


class XrayRevisionChoiceOutput(BaseOutput):
    id: int
    config_sha256: str
    created_at: datetime


class XrayRevisionSelectionMeta(BaseModel):
    next_before_id: int | None


class XrayRevisionInboundOutput(BaseOutput):
    tag: str
    protocol: str
    network: str | None
    security: str | None


class XrayRevisionOutput(BaseOutput):
    id: int
    config_sha256: str
    size_bytes: int
    created_at: datetime
