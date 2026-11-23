"""Shared storage upload errors."""


class FileTooLarge(ValueError):
    """The actual upload exceeded the storage byte limit."""
