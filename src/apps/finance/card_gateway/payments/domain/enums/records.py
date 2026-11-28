"""Payment states shown in the Finance panel."""

from enum import StrEnum


class PaymentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
