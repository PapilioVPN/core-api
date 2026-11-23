"""Measured system reads through native worker threads."""

from anyio import to_thread

from src.apps.core.system.app.helpers.measurement import measure
from src.apps.core.system.domain.results.network import (
    NetworkInterface,
    NetworkIoCounters,
)
from src.apps.core.system.domain.results.services import (
    MeasuredResult,
)
from src.apps.core.system.infra.sys.network import NetworkReader


class NetworkHealthService:
    def __init__(self, reader: NetworkReader) -> None:
        """Bind the focused reader and native thread execution.

        Args:
            reader: Synchronous system reader.


        Returns:
            None.
        """
        self.reader = reader

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
        result = await measure(to_thread.run_sync, self.reader.read_interfaces)
        return result

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
        result = await measure(
            to_thread.run_sync, self.reader.read_io_counters
        )
        return result

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
        result = await measure(
            to_thread.run_sync, self.reader.read_total_io_counters
        )
        return result
