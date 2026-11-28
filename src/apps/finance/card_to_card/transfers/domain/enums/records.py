"""How an incoming bank transfer was recorded."""

from enum import StrEnum


class TransferSource(StrEnum):
    ADMIN = "admin"
    HOOK = "hook"
