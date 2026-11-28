"""Technical counter selection and reset evidence."""

from enum import StrEnum


class ResetKind(StrEnum):
    COUNTER = "counter"
    PAIR = "pair"
    SCOPE = "scope"


class TrafficDirection(StrEnum):
    UPLINK = "uplink"
    DOWNLINK = "downlink"


class ResetState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    PARTIAL = "partial"
    NOT_APPLIED = "not_applied"
    UNKNOWN = "unknown"


class ResetEffect(StrEnum):
    ACKNOWLEDGED = "acknowledged"
    MISSING = "missing"
    NOT_APPLIED = "not_applied"
    NOT_ATTEMPTED = "not_attempted"
    UNKNOWN = "unknown"


class ResetReason(StrEnum):
    TARGET_CHANGED = "target_changed"
    NOT_CONFIGURED = "not_configured"
    TARGET_NOT_FOUND = "target_not_found"
    REJECTED = "rejected"
    RESOURCE_LIMIT = "resource_limit"
    UNSUPPORTED = "unsupported"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    INTERRUPTED = "interrupted"
    UNCONFIRMED = "unconfirmed"
    DISPATCH_EXPIRED = "dispatch_expired"
