"""Locally observed states of payment link issuance."""

from enum import StrEnum


class LinkStatus(StrEnum):
    ISSUING = "issuing"
    READY = "ready"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
