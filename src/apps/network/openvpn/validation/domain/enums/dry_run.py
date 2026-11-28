"""Stable OpenVPN candidate validation outcomes."""

from enum import StrEnum


class OpenVPNIssue(StrEnum):
    UNKNOWN = "unknown"
    INVALID_SOURCE = "invalid_source"
    UNSUPPORTED_DIRECTIVE = "unsupported_directive"
    OPTIONS_REJECTED = "options_rejected"
