"""Decode OpenVPN's native option validation result."""

from ....instances.infra.grpc.v1 import openvpn_instances_pb2 as wire
from ...domain.enums.dry_run import OpenVPNIssue
from ...domain.results.dry_run import OpenVPNValidation

WireIssue = wire.OpenVPNConfigIssueCode
_ISSUES = {
    WireIssue.OPEN_VPN_CONFIG_ISSUE_CODE_INVALID_SOURCE: (
        OpenVPNIssue.INVALID_SOURCE
    ),
    WireIssue.OPEN_VPN_CONFIG_ISSUE_CODE_UNSUPPORTED_DIRECTIVE: (
        OpenVPNIssue.UNSUPPORTED_DIRECTIVE
    ),
    WireIssue.OPEN_VPN_CONFIG_ISSUE_CODE_OPTIONS_REJECTED: (
        OpenVPNIssue.OPTIONS_REJECTED
    ),
}


def decode(
    reply: wire.OpenVPNConfigValidation, instance_id: str
) -> OpenVPNValidation | None:
    """Require the selected instance and coherent validity evidence."""
    result = None
    if reply.id == instance_id:
        if reply.valid and not reply.HasField("issue"):
            result = OpenVPNValidation(True, None, None)
        elif not reply.valid and reply.HasField("issue"):
            issue = _ISSUES.get(reply.issue.code, OpenVPNIssue.UNKNOWN)
            result = OpenVPNValidation(False, issue, reply.issue.line or None)
    return result
