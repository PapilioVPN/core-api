"""Decode Xray v1 observations without exposing native diagnostics."""

from re import fullmatch

from ...domain.enums.status import XrayInstanceState
from ...domain.enums.validation import XrayIssueCode, XrayValidationStatus
from ...domain.results.status import XrayInstanceObservation
from ...domain.results.validation import (
    XrayValidationIssue,
    XrayValidationOutcome,
)
from .v1.configs_pb2 import XrayConfigIssueCode, XrayConfigValidation
from .v1.instances_pb2 import (
    XrayInstanceState as WireState,
)
from .v1.instances_pb2 import XrayInstanceStatus

_ISSUES = {
    XrayConfigIssueCode.XRAY_CONFIG_ISSUE_CODE_CONFIG_DECODE_ERROR: (
        XrayIssueCode.CONFIG_DECODE_ERROR
    ),
    XrayConfigIssueCode.XRAY_CONFIG_ISSUE_CODE_CONFIG_REJECTED: (
        XrayIssueCode.CONFIG_REJECTED
    ),
}
_STATES = {
    WireState.XRAY_INSTANCE_STATE_STOPPED: XrayInstanceState.STOPPED,
    WireState.XRAY_INSTANCE_STATE_STARTING: XrayInstanceState.STARTING,
    WireState.XRAY_INSTANCE_STATE_READY: XrayInstanceState.READY,
    WireState.XRAY_INSTANCE_STATE_STOPPING: XrayInstanceState.STOPPING,
    WireState.XRAY_INSTANCE_STATE_FAILED: XrayInstanceState.FAILED,
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


def decode_instance(
    reply: XrayInstanceStatus, instance_id: str
) -> XrayInstanceObservation | None:
    """Accept only correlated state and evidence consistent with Node v1."""
    state = _STATES.get(reply.state)
    digest = (
        reply.applied_config_sha256
        if reply.HasField("applied_config_sha256")
        else None
    )
    observation = None
    if (
        reply.id == instance_id
        and state is not None
        and (
            digest is None
            or (
                state is XrayInstanceState.READY
                and fullmatch(r"[a-f0-9]{64}", digest) is not None
            )
        )
    ):
        observation = XrayInstanceObservation(
            state=state,
            xray_version=reply.xray_version or None,
            node_version=reply.node_version or None,
            applied_config_sha256=digest,
        )
    return observation
