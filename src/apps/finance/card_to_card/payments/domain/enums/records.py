"""Creation modes and review states for card payments."""

from enum import StrEnum


class PaymentMode(StrEnum):
    MANUAL = "manual"
    AUTO = "auto"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
