"""Read filesystems and native aggregate/per-device I/O counters."""

from datetime import UTC, datetime
from pathlib import Path

import psutil

from src.apps.core.system.health.domain.results.storage import (
    DiskIoCounters,
    DiskPartition,
    DiskUsage,
)


class DiskReader:
    def read_partitions(
        self, *, include_virtual: bool = True
    ) -> tuple[DiskPartition, ...]:
        """Read native filesystem partition metadata.

        Args:
            include_virtual: Include virtual filesystems when True.

        Returns:
            Partitions in native mount order, without raw mount options.
        """
        return tuple(
            DiskPartition(
                device=item.device,
                mountpoint=item.mountpoint,
                filesystem=item.fstype,
                read_only="ro" in item.opts.split(","),
            )
            for item in psutil.disk_partitions(all=include_virtual)
        )

    def read_usage(self, path: Path) -> DiskUsage:
        """Read filesystem usage for one existing absolute path.

        Args:
            path: Absolute path on the filesystem to inspect.

        Returns:
            Resolved path and total, used and free space in bytes.

        Raises:
            ValueError: The supplied path is relative.
            OSError: Path resolution or filesystem access fails.
        """
        if not path.is_absolute():
            raise ValueError("path must be absolute")
        resolved = path.resolve(strict=True)
        usage = psutil.disk_usage(str(resolved))
        return DiskUsage(
            observed_at=datetime.now(UTC),
            path=str(resolved),
            total_bytes=usage.total,
            used_bytes=usage.used,
            free_bytes=usage.free,
            percent=usage.percent,
        )

    def read_io_counters(self) -> tuple[DiskIoCounters, ...] | None:
        """Read native cumulative disk I/O counters per device.

        Args:
            None.

        Returns:
            Counters ordered by device name, or None if unavailable.
            Sizes are bytes and I/O durations are milliseconds.
        """
        counters = psutil.disk_io_counters(perdisk=True)
        result: tuple[DiskIoCounters, ...] | None = None
        if counters is not None:
            observed_at = datetime.now(UTC)
            result = tuple(
                DiskIoCounters(
                    observed_at=observed_at,
                    device=name,
                    read_count=counters[name].read_count,
                    write_count=counters[name].write_count,
                    read_bytes=counters[name].read_bytes,
                    write_bytes=counters[name].write_bytes,
                    read_time_ms=counters[name].read_time,
                    write_time_ms=counters[name].write_time,
                    read_merged_count=counters[name].read_merged_count
                    if psutil.LINUX
                    else None,
                    write_merged_count=counters[name].write_merged_count
                    if psutil.LINUX
                    else None,
                    busy_time_ms=counters[name].busy_time
                    if psutil.LINUX
                    else None,
                )
                for name in sorted(counters)
            )
        return result

    def read_total_io_counters(self) -> DiskIoCounters | None:
        """Read native cumulative disk I/O totals.

        Args:
            None.

        Returns:
            Aggregate counters with device=None, or None if unavailable.
            Sizes are bytes and I/O durations are milliseconds.
        """
        counters = psutil.disk_io_counters()
        result: DiskIoCounters | None = None
        if counters is not None:
            result = DiskIoCounters(
                observed_at=datetime.now(UTC),
                device=None,
                read_count=counters.read_count,
                write_count=counters.write_count,
                read_bytes=counters.read_bytes,
                write_bytes=counters.write_bytes,
                read_time_ms=counters.read_time,
                write_time_ms=counters.write_time,
                read_merged_count=counters.read_merged_count
                if psutil.LINUX
                else None,
                write_merged_count=counters.write_merged_count
                if psutil.LINUX
                else None,
                busy_time_ms=counters.busy_time if psutil.LINUX else None,
            )
        return result
