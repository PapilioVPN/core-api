"""States of observations recorded by the Xray Observatory."""

from enum import StrEnum


class XrayOutboundState(StrEnum):
    HEALTHY = "healthy"
    FAILED = "failed"
    NO_SAMPLE = "no_sample"
