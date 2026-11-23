"""Interface metadata and cumulative network counters."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class InterfaceAddress:
    family: int
    address: str
    netmask: str | None
    broadcast: str | None
    point_to_point: str | None


@dataclass(frozen=True, slots=True)
class InterfaceStatus:
    is_up: bool
    duplex: int
    speed_mbps: int
    mtu_bytes: int
    flags: str


@dataclass(frozen=True, slots=True)
class NetworkInterface:
    name: str
    addresses: tuple[InterfaceAddress, ...]
    status: InterfaceStatus | None


@dataclass(frozen=True, slots=True)
class NetworkIoCounters:
    observed_at: datetime
    interface: str | None
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    errors_in: int
    errors_out: int
    dropped_in: int
    dropped_out: int
