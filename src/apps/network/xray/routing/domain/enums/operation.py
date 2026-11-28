"""Actions and delivery evidence of a live routing mutation."""

from enum import StrEnum


class RoutingAction(StrEnum):
    APPEND = "append_rule"
    REPLACE = "replace_rules"
    REMOVE = "remove_rule"
    OVERRIDE = "set_override"
    CLEAR = "clear_override"


class RoutingState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    UNKNOWN = "unknown"


class RoutingFailure(StrEnum):
    TARGET_CHANGED = "target_changed"
    NOT_CONFIGURED = "not_configured"
    PAYLOAD_UNAVAILABLE = "payload_unavailable"
    TARGET_NOT_FOUND = "target_not_found"
    ALREADY_EXISTS = "already_exists"
    FENCED = "fenced"
    RESOURCE_LIMIT = "resource_limit"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    UNCONFIRMED = "unconfirmed"
    DISPATCH_EXPIRED = "dispatch_expired"
