"""Decode Node's Hysteria preflight evidence."""

from ...domain.enums.dry_run import HysteriaIssue
from ...domain.results.dry_run import HysteriaValidation
from .v1.hysteria_configs_pb2 import HysteriaConfigValidation

_ISSUES = {issue.value: issue for issue in HysteriaIssue}


def decode(
    reply: HysteriaConfigValidation, instance_id: str
) -> HysteriaValidation | None:
    """Require the selected instance and the known preflight scope."""
    result = None
    if reply.id == instance_id and reply.scope == "node_preflight":
        if reply.valid and not reply.issue:
            result = HysteriaValidation(True, None, "node_preflight")
        elif not reply.valid and reply.issue:
            issue = _ISSUES.get(reply.issue, HysteriaIssue.UNKNOWN)
            result = HysteriaValidation(False, issue, "node_preflight")
    return result
