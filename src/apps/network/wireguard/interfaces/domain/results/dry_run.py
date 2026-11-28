"""Observed WireGuard validation evidence."""

from dataclasses import dataclass

from ..enums.dry_run import WireGuardIssue


@dataclass(frozen=True, slots=True)
class WireGuardValidation:
    valid: bool
    issue: WireGuardIssue | None
