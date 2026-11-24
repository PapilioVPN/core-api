"""Independent review state of submitted bank evidence."""

from enum import StrEnum


class ReceiptStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
