"""Panel outcomes for a single observation from a configured Node."""

from enum import StrEnum


class NodeReadStatus(StrEnum):
    OBSERVED = "observed"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    TARGET_NOT_FOUND = "target_not_found"
    BUSY = "busy"
    RESOURCE_LIMIT = "resource_limit"
    PRECONDITION_FAILED = "precondition_failed"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class NodeInstanceState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    STOPPING = "stopping"
    FAILED = "failed"
