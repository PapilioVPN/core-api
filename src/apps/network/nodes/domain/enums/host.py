"""Outcomes of a single live host observation."""

from enum import StrEnum


class HostStatsStatus(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
