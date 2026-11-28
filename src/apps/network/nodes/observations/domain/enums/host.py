"""Outcomes of a live host observation."""

from enum import StrEnum


class HostStatsStatus(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    DISABLED = "disabled"
    NODE_NOT_FOUND = "node_not_found"
    BUSY = "busy"
    NOT_CONFIGURED = "not_configured"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
