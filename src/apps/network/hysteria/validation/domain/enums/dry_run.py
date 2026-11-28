"""Stable Hysteria candidate validation outcomes."""

from enum import StrEnum


class HysteriaIssue(StrEnum):
    UNKNOWN = "unknown"
    INVALID_YAML = "invalid_yaml"
    UNSUPPORTED_SOURCE = "unsupported_source"
    INVALID_LISTENER = "invalid_listener"
    INVALID_TRAFFIC_STATS = "invalid_traffic_stats"
    INVALID_TLS = "invalid_tls"
    INVALID_AUTH = "invalid_auth"
