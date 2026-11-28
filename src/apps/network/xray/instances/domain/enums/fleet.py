"""Per-target decisions without conflating admission and execution."""

from enum import StrEnum


class XrayFleetOperationStatus(StrEnum):
    ACCEPTED = "accepted"
    NODE_NOT_FOUND = "node_not_found"
    NODE_DISABLED = "node_disabled"
    ACTIVE_OPERATION = "active_operation"
    REQUEST_CONFLICT = "request_conflict"
    OPERATION_NOT_FOUND = "operation_not_found"
