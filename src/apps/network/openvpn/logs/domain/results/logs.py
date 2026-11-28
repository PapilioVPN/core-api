"""Ordered OpenVPN log batches and the gap preceding each batch."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpenVPNLogLine:
    sequence: int
    timestamp_unix_seconds: int
    level: str
    message: str


@dataclass(frozen=True, slots=True)
class OpenVPNLogBatch:
    execution_id: str
    dropped: int
    entries: tuple[OpenVPNLogLine, ...]
