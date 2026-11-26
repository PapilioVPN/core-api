"""Direction of a posted wallet movement."""

from enum import StrEnum


class Direction(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"
