"""Payment origins and lifecycle states."""

from enum import StrEnum


class PaymentSource(StrEnum):
    WALLET_TOPUP = "wallet_topup"
    ORDER_PAYMENT = "order_payment"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
