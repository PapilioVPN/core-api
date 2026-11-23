"""Counts and time bounds over matching audit search text."""

from dataclasses import dataclass
from datetime import datetime

from src.apps.core.audit.domain.enums.actions import AuditAction


@dataclass(frozen=True, slots=True)
class AuditOptions:
    actors: dict[int, int]
    actions: dict[AuditAction, int]
    first: datetime | None
    last: datetime | None
