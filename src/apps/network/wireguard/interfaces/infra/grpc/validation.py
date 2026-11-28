"""Decode WireGuard configuration issues without exposing source."""

from ...domain.enums.dry_run import WireGuardIssue
from ...domain.results.dry_run import WireGuardValidation
from .v1.interfaces_pb2 import WireGuardConfigIssue as WireIssue
from .v1.interfaces_pb2 import WireGuardConfigValidation

_ISSUES = {
    WireIssue.WIRE_GUARD_CONFIG_ISSUE_INVALID_JSON: (
        WireGuardIssue.INVALID_JSON
    ),
    WireIssue.WIRE_GUARD_CONFIG_ISSUE_INVALID_PRIVATE_KEY: (
        WireGuardIssue.INVALID_PRIVATE_KEY
    ),
    WireIssue.WIRE_GUARD_CONFIG_ISSUE_INVALID_ADDRESSES: (
        WireGuardIssue.INVALID_ADDRESSES
    ),
    WireIssue.WIRE_GUARD_CONFIG_ISSUE_DUPLICATE_ADDRESS: (
        WireGuardIssue.DUPLICATE_ADDRESS
    ),
    WireIssue.WIRE_GUARD_CONFIG_ISSUE_INVALID_MTU: (
        WireGuardIssue.INVALID_MTU
    ),
    WireIssue.WIRE_GUARD_CONFIG_ISSUE_INVALID_LISTEN_PORT: (
        WireGuardIssue.INVALID_LISTEN_PORT
    ),
    WireIssue.WIRE_GUARD_CONFIG_ISSUE_INVALID_INITIAL_PEERS: (
        WireGuardIssue.INVALID_INITIAL_PEERS
    ),
}


def decode(reply: WireGuardConfigValidation) -> WireGuardValidation | None:
    """Distinguish a checked source from an inconsistent reply."""
    result = None
    if (
        reply.valid
        and reply.issue == WireIssue.WIRE_GUARD_CONFIG_ISSUE_UNSPECIFIED
    ):
        result = WireGuardValidation(True, None)
    elif (
        not reply.valid
        and reply.issue != WireIssue.WIRE_GUARD_CONFIG_ISSUE_UNSPECIFIED
    ):
        result = WireGuardValidation(
            False, _ISSUES.get(reply.issue, WireGuardIssue.UNKNOWN)
        )
    return result
