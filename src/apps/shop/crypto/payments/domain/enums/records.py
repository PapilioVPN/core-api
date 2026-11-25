"""Internal crypto payment states independent of the gateway."""

from enum import StrEnum


class CryptoPaymentStatus(StrEnum):
    PENDING = "pending"
    PARTIAL = "partial"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    EXPIRED = "expired"
