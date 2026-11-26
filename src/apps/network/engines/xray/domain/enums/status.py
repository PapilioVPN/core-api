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
    INSTANCE_NOT_FOUND = "instance_not_found"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
