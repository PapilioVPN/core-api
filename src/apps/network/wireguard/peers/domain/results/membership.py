"""Observed public WireGuard peer membership."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WireGuardPeer:
    public_key: str
    allowed_ips: tuple[str, ...]
