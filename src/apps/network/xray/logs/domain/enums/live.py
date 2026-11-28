"""Source and terminal outcomes of a selected Xray log stream."""

from enum import StrEnum


class XrayLogSource(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"
    UNSPECIFIED = "unspecified"


class XrayLogEnd(StrEnum):
    ENDED = "ended"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    NOT_FOUND = "not_found"
    NOT_RUNNING = "not_running"
    BUSY = "busy"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    REJECTED = "rejected"
    INTERRUPTED = "interrupted"
