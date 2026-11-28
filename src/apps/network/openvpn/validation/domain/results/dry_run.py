"""Observed OpenVPN validation evidence."""

from dataclasses import dataclass

from ..enums.dry_run import OpenVPNIssue


@dataclass(frozen=True, slots=True)
class OpenVPNValidation:
    valid: bool
    issue: OpenVPNIssue | None
    line: int | None
