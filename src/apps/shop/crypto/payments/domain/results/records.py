"""Expected provider outcomes for a cryptocurrency payment."""

from enum import StrEnum


class PaymentFailure(StrEnum):
    INVOICE_UNAVAILABLE = "invoice_unavailable"
    CHECK_UNAVAILABLE = "check_unavailable"
    INVALID_NOTIFICATION = "invalid_notification"
    INVOICE_MISMATCH = "invoice_mismatch"
