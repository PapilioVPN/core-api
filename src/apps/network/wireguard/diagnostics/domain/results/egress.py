"""Reachability reported by the Node's configured WireGuard egress probe."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WireGuardEgress:
    reachable: bool
    http_status: int | None
    elapsed_nanoseconds: int
    observed_at_unix_nanoseconds: int
