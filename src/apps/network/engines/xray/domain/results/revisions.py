"""Immutable revision views that separate source from metadata."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class XrayRevision:
    id: int
    config_sha256: str
    size_bytes: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class XrayRevisionSave:
    revision: XrayRevision
    created: bool


@dataclass(frozen=True, slots=True)
class XrayRevisionSource:
    config_sha256: str
    config_json: bytes = field(repr=False)
