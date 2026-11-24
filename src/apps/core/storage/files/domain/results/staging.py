"""Metadata for a prepared file with a context-owned temporary lifetime."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StagedFile:
    path: Path
    sha256: str
    size_bytes: int
