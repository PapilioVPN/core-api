"""Credential-free metadata for the panel's stored revision catalog."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class XrayRevisionOutput(BaseOutput):
    id: int
    config_sha256: str
    size_bytes: int
    created_at: datetime
