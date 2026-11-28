"""Observed lifecycle states and status query outcomes."""

from enum import StrEnum


class XrayInstanceState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    STOPPING = "stopping"
    FAILED = "failed"


class XrayStatusCode(StrEnum):
    OBSERVED = "observed"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    NODE_NOT_FOUND = "node_not_found"
    INSTANCE_NOT_FOUND = "instance_not_found"
    BUSY = "busy"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
