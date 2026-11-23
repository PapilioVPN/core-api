"""Measured system reads through native worker threads."""

from anyio import to_thread

from src.apps.core.system.app.helpers.measurement import measure
from src.apps.core.system.domain.results.resources import (
    CoreCpuUsage,
    CpuInfo,
    CpuUsage,
    HostInfo,
    MemoryInfo,
    RuntimeInfo,
    SwapInfo,
    UserSession,
)
from src.apps.core.system.domain.results.services import (
    MeasuredResult,
)
from src.apps.core.system.infra.sys.resources import (
    SystemResourcesReader,
)


class SystemResourcesService:
    def __init__(self, reader: SystemResourcesReader) -> None:
        """Bind the focused reader and native thread execution.

        Args:
            reader: Synchronous system reader.


        Returns:
            None.
        """
        self.reader = reader

    async def read_host(self) -> MeasuredResult[HostInfo]:
        """Read OS identity, boot time and uptime without blocking the loop.

        Args:
            None.

        Returns:
            Host metadata and elapsed milliseconds; uptime is seconds.
        """
        result = await measure(to_thread.run_sync, self.reader.read_host)
        return result

    async def read_runtime(self) -> MeasuredResult[RuntimeInfo]:
        """Read the API process's Python runtime information.

        Args:
            None.

        Returns:
            API runtime metadata and elapsed milliseconds.
        """
        result = await measure(to_thread.run_sync, self.reader.read_runtime)
        return result

    async def read_sessions(self) -> MeasuredResult[tuple[UserSession, ...]]:
        """Read OS login sessions without blocking the loop.

        Args:
            None.

        Returns:
            Sessions in native order and elapsed milliseconds.
        """
        result = await measure(to_thread.run_sync, self.reader.read_sessions)
        return result

    async def read_cpu(self) -> MeasuredResult[CpuInfo]:
        """Read CPU topology, frequencies and cumulative counters.

        Args:
            None.

        Returns:
            CPU metadata and elapsed milliseconds; unavailable fields are None.
            CPU times are seconds and frequencies are MHz.
        """
        result = await measure(to_thread.run_sync, self.reader.read_cpu)
        return result

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
        result = await measure(
            to_thread.run_sync, self.reader.read_cpu_usage, sample_seconds
        )
        return result

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
        result = await measure(
            to_thread.run_sync, self.reader.read_core_usage, sample_seconds
        )
        return result

    async def read_memory(self) -> MeasuredResult[MemoryInfo]:
        """Read OS-visible physical memory information.

        Args:
            None.

        Returns:
            Byte counts, utilization and elapsed milliseconds. Unavailable
            platform-specific fields remain None.
        """
        result = await measure(to_thread.run_sync, self.reader.read_memory)
        return result

    async def read_swap(self) -> MeasuredResult[SwapInfo]:
        """Read OS-visible swap usage and cumulative I/O.

        Args:
            None.

        Returns:
            Byte counts, utilization and elapsed milliseconds.
        """
        result = await measure(to_thread.run_sync, self.reader.read_swap)
        return result
