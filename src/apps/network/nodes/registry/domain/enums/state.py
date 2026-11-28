"""Local outcomes of a registry enable or disable request."""

from enum import StrEnum


class NodeStateStatus(StrEnum):
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    NODE_NOT_FOUND = "node_not_found"
