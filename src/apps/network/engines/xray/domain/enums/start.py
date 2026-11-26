"""Persisted states and machine-readable outcomes for a configured start."""

from enum import StrEnum


class XrayStartState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class XrayStartReason(StrEnum):
    TARGET_CHANGED = "target_changed"
    NOT_CONFIGURED = "not_configured"
    INSTANCE_NOT_FOUND = "instance_not_found"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    BUSY = "busy"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    UNCONFIRMED = "unconfirmed"
    DISPATCH_EXPIRED = "dispatch_expired"
