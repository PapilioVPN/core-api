"""Decode the Xray v1 validation reply without exposing diagnostic text."""

from ...domain.enums.validation import XrayIssueCode, XrayValidationStatus
from ...domain.results.validation import (
    XrayValidationIssue,
    XrayValidationOutcome,
)
from .v1.configs_pb2 import XrayConfigIssueCode, XrayConfigValidation

_ISSUES = {
    XrayConfigIssueCode.XRAY_CONFIG_ISSUE_CODE_CONFIG_DECODE_ERROR: (
        XrayIssueCode.CONFIG_DECODE_ERROR
    ),
    XrayConfigIssueCode.XRAY_CONFIG_ISSUE_CODE_CONFIG_REJECTED: (
        XrayIssueCode.CONFIG_REJECTED
    ),
}


def decode_validation(
    reply: XrayConfigValidation, instance_id: str
) -> XrayValidationOutcome:
    """Correlate the reply and preserve native issue codes and locations."""
    outcome = XrayValidationOutcome(XrayValidationStatus.FAILED)
    if reply.id == instance_id:
        has_issue = reply.HasField("issue")
        if reply.valid and not has_issue:
            outcome = XrayValidationOutcome(XrayValidationStatus.VALID)
        elif not reply.valid and has_issue:
            issue = reply.issue
            outcome = XrayValidationOutcome(
                XrayValidationStatus.INVALID,
                XrayValidationIssue(
                    code=_ISSUES.get(issue.code, XrayIssueCode.UNKNOWN),
                    line=issue.line or None,
                    column=issue.column or None,
                ),
            )
    return outcome
