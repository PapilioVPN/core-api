"""Observed Hysteria validation evidence."""

from dataclasses import dataclass
from typing import Literal

from ..enums.dry_run import HysteriaIssue


@dataclass(frozen=True, slots=True)
class HysteriaValidation:
    valid: bool
    issue: HysteriaIssue | None
    scope: Literal["node_preflight"]
