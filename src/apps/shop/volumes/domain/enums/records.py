"""Kinds of reusable volume definitions."""

from enum import StrEnum


class VolumeMode(StrEnum):
    FIXED = "fixed"
    CUSTOM = "custom"
