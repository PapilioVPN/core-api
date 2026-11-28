"""Removal outcome correlated with a requested revision identity."""

from dataclasses import dataclass

from ..enums.removal import XrayRevisionRemovalStatus


@dataclass(frozen=True, slots=True)
class XrayRevisionRemoval:
    revision_id: int
    status: XrayRevisionRemovalStatus
