"""Outcomes of a completed receipt extraction attempt."""

from enum import StrEnum


class ExtractionStatus(StrEnum):
    EXTRACTED = "extracted"
    UNREADABLE = "unreadable"
    FAILED = "failed"
