"""Typed service contracts for local system information."""

from pathlib import Path
from typing import Protocol

from src.apps.core.system.health.domain.results.services import MeasuredResult
from src.apps.core.system.info.domain.results.network import (
    NetworkInterface,
    NetworkIoCounters,
)
from src.apps.core.system.info.domain.results.processes import (
    ProcessInfo,
    ProcessListing,
)
from src.apps.core.system.info.domain.results.resources import (
    CoreCpuUsage,
    CpuInfo,
    CpuUsage,
    HostInfo,
    MemoryInfo,
    RuntimeInfo,
    SwapInfo,
    UserSession,
)
from src.apps.core.system.info.domain.results.sensors import (
    BatteryInfo,
    FanSpeed,
    Temperature,
)
from src.apps.core.system.info.domain.results.storage import (
    DiskIoCounters,
    DiskPartition,
    DiskUsage,
)


class ISystemResourcesService(Protocol):
    async def read_host(self) -> MeasuredResult[HostInfo]:
        """Read OS identity, boot time and uptime without blocking the loop.

        Args:
            None.

        Returns:
            Host metadata and elapsed milliseconds; uptime is seconds.
        """
        ...

    async def read_runtime(self) -> MeasuredResult[RuntimeInfo]:
        """Read the API process's Python runtime information.

        Args:
            None.

        Returns:
            API runtime metadata and elapsed milliseconds.
        """
        ...

    async def read_sessions(self) -> MeasuredResult[tuple[UserSession, ...]]:
        """Read OS login sessions without blocking the loop.

        Args:
            None.

        Returns:
            Sessions in native order and elapsed milliseconds.
        """
        ...

    async def read_cpu(self) -> MeasuredResult[CpuInfo]:
        """Read CPU topology, frequencies and cumulative counters.

        Args:
            None.

        Returns:
            CPU metadata and elapsed milliseconds; unavailable fields are None.
            CPU times are seconds and frequencies are MHz.
        """
        ...

    async def read_cpu_usage(
        self, sample_seconds: float
    ) -> MeasuredResult[CpuUsage]:
        """Sample total CPU utilization without blocking the event loop.

        Args:
            sample_seconds: Positive finite native sampling interval, seconds.

        Returns:
            CPU percentage and requested interval, with elapsed milliseconds.

        Raises:
            ValueError: The interval is not positive and finite.
        """
        ...

    async def read_core_usage(
        self, sample_seconds: float
    ) -> MeasuredResult[CoreCpuUsage]:
        """Sample individual CPU cores without blocking the event loop.

        Args:
            sample_seconds: Positive finite native sampling interval, seconds.

        Returns:
            Percentages in native core order, requested interval and elapsed
            milliseconds; the interval is distinct from measured duration.

        Raises:
            ValueError: The interval is not positive and finite.
        """
        ...

    async def read_memory(self) -> MeasuredResult[MemoryInfo]:
        """Read OS-visible physical memory information.

        Args:
            None.

        Returns:
            Byte counts, utilization and elapsed milliseconds. Unavailable
            platform-specific fields remain None.
        """
        ...

    async def read_swap(self) -> MeasuredResult[SwapInfo]:
        """Read OS-visible swap usage and cumulative I/O.

        Args:
            None.

        Returns:
            Byte counts, utilization and elapsed milliseconds.
        """
        ...


class IDiskService(Protocol):
    async def read_partitions(
        self, *, include_virtual: bool = True
    ) -> MeasuredResult[tuple[DiskPartition, ...]]:
        """Read filesystem partition metadata without blocking the loop.

        Args:
            include_virtual: Include virtual filesystems when True.

        Returns:
            Partitions in native mount order and elapsed milliseconds.
        """
        ...

    async def read_usage(self, path: Path) -> MeasuredResult[DiskUsage]:
        """Read usage for the filesystem containing an existing absolute path.

        Args:
            path: Absolute existing path on the API host.

        Returns:
            Resolved path, byte counts, utilization and elapsed milliseconds.

        Raises:
            ValueError: The path is relative.
            OSError: Path resolution or filesystem access fails.
        """
        ...

    async def read_io_counters(
        self,
    ) -> MeasuredResult[tuple[DiskIoCounters, ...] | None]:
        """Read cumulative disk I/O per device without blocking the loop.

        Args:
            None.

        Returns:
            Counters ordered by device, or None if unavailable, with elapsed
            milliseconds. Counter durations are also milliseconds.
        """
        ...

    async def read_total_io_counters(
        self,
    ) -> MeasuredResult[DiskIoCounters | None]:
        """Read cumulative total disk I/O without blocking the loop.

        Args:
            None.

        Returns:
            Counters with device=None, or None if unavailable, and elapsed
            milliseconds. Counter durations are also milliseconds.
        """
        ...


class INetworkService(Protocol):
    async def read_interfaces(
        self,
    ) -> MeasuredResult[tuple[NetworkInterface, ...]]:
        """Read network addresses and interface status.

        Args:
            None.

        Returns:
            Interfaces ordered by name and elapsed milliseconds. Unavailable
            status remains None; link speeds use Mbps and sizes use bytes.
        """
        ...

    async def read_io_counters(
        self,
    ) -> MeasuredResult[tuple[NetworkIoCounters, ...] | None]:
        """Read cumulative network I/O per interface.

        Args:
            None.

        Returns:
            Counters ordered by interface, or None if unavailable, with elapsed
            milliseconds. Counter values remain byte and packet/error counts.
        """
        ...

    async def read_total_io_counters(
        self,
    ) -> MeasuredResult[NetworkIoCounters | None]:
        """Read cumulative total network I/O.

        Args:
            None.

        Returns:
            Counters with interface=None, or None if unavailable, and elapsed
            milliseconds. Counter values remain byte and packet/error counts.
        """
        ...


class IProcessService(Protocol):
    async def read_process(
        self, process_id: int
    ) -> MeasuredResult[ProcessInfo | None]:
        """Read one process's metadata without blocking the loop.

        Args:
            process_id: Positive operating-system process identifier.

        Returns:
            Process metadata or None if it has exited, with elapsed
            milliseconds. Inaccessible attributes remain None.

        Raises:
            ValueError: The identifier is not positive.
        """
        ...

    async def read_processes(
        self, *, limit: int
    ) -> MeasuredResult[ProcessListing]:
        """Read a bounded listing of observable processes.

        Args:
            limit: Positive maximum number of process records.

        Returns:
            Records ordered by PID with truncation, and elapsed milliseconds.
            Inaccessible attributes remain None.

        Raises:
            ValueError: The limit is not positive.
        """
        ...

    async def read_process_count(self) -> MeasuredResult[int]:
        """Read the number of observable processes without blocking the loop.

        Args:
            None.

        Returns:
            Native process count and elapsed milliseconds.
        """
        ...


class ISensorService(Protocol):
    async def read_temperatures(
        self,
    ) -> MeasuredResult[tuple[Temperature, ...] | None]:
        """Read supported temperature sensors without blocking the loop.

        Args:
            None.

        Returns:
            Celsius readings in device-name/native reading order, or None on
            unsupported platforms, with elapsed milliseconds. A supported
            platform without readings yields an empty tuple.
        """
        ...

    async def read_fans(
        self,
    ) -> MeasuredResult[tuple[FanSpeed, ...] | None]:
        """Read supported fan speed sensors without blocking the loop.

        Args:
            None.

        Returns:
            RPM readings in device-name/native reading order, or None on
            unsupported platforms, with elapsed milliseconds. A supported
            platform without readings yields an empty tuple.
        """
        ...

    async def read_battery(self) -> MeasuredResult[BatteryInfo | None]:
        """Read battery status without blocking the event loop.

        Args:
            None.

        Returns:
            Battery metadata, or None if absent/unsupported, and elapsed
            milliseconds. Unknown/unlimited remaining seconds stay None.
        """
        ...
