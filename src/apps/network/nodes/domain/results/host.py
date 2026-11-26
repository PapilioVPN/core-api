"""Host observations independent of database and wire types."""

from dataclasses import dataclass
from datetime import datetime

from ..enums.host import HostStatsStatus


@dataclass(frozen=True, slots=True)
class HostCPU:
    busy_percent: float
    steal_percent: float | None
    window_milliseconds: int
    observed_at: datetime | None


@dataclass(frozen=True, slots=True)
class HostMemory:
    total_bytes: int
    available_bytes: int | None
    used_bytes: int | None
    swap_total_bytes: int
    swap_free_bytes: int


@dataclass(frozen=True, slots=True)
class HostStorage:
    path: str
    total_bytes: int
    used_bytes: int
    available_bytes: int
    read_only: bool


@dataclass(frozen=True, slots=True)
class HostNetwork:
    rx_bytes_per_second: int
    tx_bytes_per_second: int
    window_milliseconds: int
    observed_at: datetime | None


@dataclass(frozen=True, slots=True)
class HostStats:
    uptime_seconds: int | None
    logical_cpu_count: int | None
    cpu: HostCPU | None
    memory: HostMemory | None
    storage: HostStorage | None
    network: HostNetwork | None

    @property
    def is_partial(self) -> bool:
        """A top-level observation is absent from Node's reply."""
        return (
            self.uptime_seconds is None
            or self.logical_cpu_count is None
            or self.cpu is None
            or self.memory is None
            or self.storage is None
            or self.network is None
        )


@dataclass(frozen=True, slots=True)
class HostStatsResult:
    status: HostStatsStatus
    stats: HostStats | None = None
    received_at: datetime | None = None
