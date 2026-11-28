"""Terminal outcomes of an authorized Node log stream."""

from enum import StrEnum


class LogStreamEnd(StrEnum):
    ENDED = "ended"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    NOT_FOUND = "not_found"
    NOT_RUNNING = "not_running"
    PRECONDITION_FAILED = "precondition_failed"
    BUSY = "busy"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    REJECTED = "rejected"
    INTERRUPTED = "interrupted"
