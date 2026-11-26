"""Machine-readable outcomes of an Xray config dry run."""

from enum import StrEnum


class XrayValidationStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    INSTANCE_NOT_FOUND = "instance_not_found"
    BUSY = "busy"
    RESOURCE_LIMIT = "resource_limit"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class XrayIssueCode(StrEnum):
    CONFIG_DECODE_ERROR = "config_decode_error"
    CONFIG_REJECTED = "config_rejected"
    UNKNOWN = "unknown"
