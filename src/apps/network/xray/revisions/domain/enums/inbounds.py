"""Failures specific to reading declared inbound choices."""

from enum import StrEnum


class XrayRevisionInboundFailure(StrEnum):
    INVALID = "xray_revision_inbounds_invalid"
