"""Modes supported by the destination card configuration."""

from enum import StrEnum


class PaymentMode(StrEnum):
    MANUAL = "manual"
    AUTO = "auto"
