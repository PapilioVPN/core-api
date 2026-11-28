"""Observed WireGuard status evidence."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WireGuardStatus:
    up: bool
    mtu: int
    interface_index: int | None
    node_version: str | None
    kernel_release: str | None
    wireguard_tools_version: str | None
    applied_config_sha256: str | None
