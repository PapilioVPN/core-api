"""Xray validation facts without any configuration contents."""

from dataclasses import dataclass

from ..enums.validation import XrayIssueCode, XrayValidationStatus


@dataclass(frozen=True, slots=True)
class XrayValidationIssue:
    code: XrayIssueCode
    line: int | None
    column: int | None


@dataclass(frozen=True, slots=True)
class XrayValidationOutcome:
    status: XrayValidationStatus
    issue: XrayValidationIssue | None = None


@dataclass(frozen=True, slots=True)
class XrayConfigValidation:
    node_id: int
    instance_id: str
    config_sha256: str
    status: XrayValidationStatus
    issue: XrayValidationIssue | None
