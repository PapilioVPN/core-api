"""Observed traffic distinguishes zero from an absent direction."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class XrayTraffic:
    name: str
    uplink_bytes: int | None
    downlink_bytes: int | None
