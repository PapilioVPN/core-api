"""WireGuard diagnostic events emitted by the selected interface."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WireGuardLogEvent:
    sequence: int
    observed_at_unix_nanoseconds: int
    kind: str
