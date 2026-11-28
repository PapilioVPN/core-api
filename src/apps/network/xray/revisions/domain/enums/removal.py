"""Outcomes of removing an immutable Xray revision."""

from enum import StrEnum


class XrayRevisionRemovalStatus(StrEnum):
    DELETED = "deleted"
    IN_USE = "in_use"
    NOT_FOUND = "not_found"
