"""Connection states reported by the node registry."""

from enum import StrEnum


class NodeConnectionStatus(StrEnum):
    UNCHECKED = "unchecked"
    REACHABLE = "reachable"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
