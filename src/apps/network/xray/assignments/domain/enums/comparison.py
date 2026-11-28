"""Observed comparison of desired and running Xray source bytes."""

from enum import StrEnum


class XrayRevisionComparisonState(StrEnum):
    UNASSIGNED = "unassigned"
    MATCHED = "matched"
    DIFFERENT = "different"
    STOPPED = "stopped"
    UNKNOWN = "unknown"
