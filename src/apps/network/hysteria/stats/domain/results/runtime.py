"""Execution identity, readiness time and uptime for one Hysteria instance."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HysteriaRuntime:
    execution: int
    ready_since_unix_nanoseconds: int
    uptime_seconds: int
