"""Events that start a subscription's validity period."""

from enum import StrEnum


class DurationStart(StrEnum):
    READY = "ready"
