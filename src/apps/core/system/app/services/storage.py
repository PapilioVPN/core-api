"""Measured system reads through native worker threads."""

from functools import partial
from pathlib import Path

from anyio import to_thread

from src.apps.core.system.app.helpers.measurement import measure
from src.apps.core.system.domain.results.services import (
    MeasuredResult,
)
from src.apps.core.system.domain.results.storage import (
    DiskIoCounters,
    DiskPartition,
    DiskUsage,
)
from src.apps.core.system.infra.sys.storage import DiskReader


class DiskHealthService:
    def __init__(self, reader: DiskReader) -> None:
        """Bind the focused reader and native thread execution.

        Args:
            reader: Synchronous system reader.


        Returns:
            None.
        """
        self.reader = reader

    async def read_partitions(
        self, *, include_virtual: bool = True
    ) -> MeasuredResult[tuple[DiskPartition, ...]]:
        """Read filesystem partition metadata without blocking the loop.

        Args:
            include_virtual: Include virtual filesystems when True.

        Returns:
            Partitions in native mount order and elapsed milliseconds.
        """
        result = await measure(
            to_thread.run_sync,
            partial(
                self.reader.read_partitions, include_virtual=include_virtual
            ),
        )
        return result

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
        result = await measure(
            to_thread.run_sync, self.reader.read_usage, path
        )
        return result

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
        result = await measure(
            to_thread.run_sync, self.reader.read_io_counters
        )
        return result

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
        result = await measure(
            to_thread.run_sync, self.reader.read_total_io_counters
        )
        return result
