"""Interface metadata and cumulative network counters."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class AddressOutput(BaseOutput):
    family: int
    address: str
    netmask: str | None
    broadcast: str | None
    point_to_point: str | None


class InterfaceStatusOutput(BaseOutput):
    is_up: bool
    duplex: int
    speed_mbps: int
    mtu_bytes: int
    flags: str


class InterfaceOutput(BaseOutput):
    name: str
    addresses: tuple[AddressOutput, ...]
    status: InterfaceStatusOutput | None


class NetworkIoOutput(BaseOutput):
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
