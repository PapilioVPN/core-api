"""Read host-visible OS resources using native psutil calls.

These are observations of the current OS namespace, not container quotas.
CPU times are cumulative seconds; CPU usage uses a real sampling interval.
"""

import os
import platform
import sys
from datetime import UTC, datetime
from math import isfinite
from time import time

import psutil

from src.apps.core.system.info.domain.results.resources import (
    CoreCpuUsage,
    CpuFrequency,
    CpuInfo,
    CpuTimes,
    CpuUsage,
    HostInfo,
    MemoryInfo,
    RuntimeInfo,
    SwapInfo,
    UserSession,
)


class SystemResourcesReader:
    def read_host(self) -> HostInfo:
        """Read OS identity, boot time and uptime visible to this process.

        Args:
            None.

        Returns:
            Host metadata with UTC timestamps and uptime in seconds.
        """
        host = platform.uname()
        boot = psutil.boot_time()
        return HostInfo(
            observed_at=datetime.now(UTC),
            hostname=host.node,
            operating_system=host.system,
            release=host.release,
            version=host.version,
            machine=host.machine,
            booted_at=datetime.fromtimestamp(boot, UTC),
            uptime_seconds=time() - boot,
        )

    def read_runtime(self) -> RuntimeInfo:
        """Read Python runtime and current process metadata.

        Args:
            None.

        Returns:
            Python identity, executable, process identity and UTC start time.
        """
        process = psutil.Process()
        return RuntimeInfo(
            observed_at=datetime.now(UTC),
            python_version=platform.python_version(),
            implementation=platform.python_implementation(),
            compiler=platform.python_compiler(),
            executable=sys.executable,
            process_id=process.pid,
            process_started_at=datetime.fromtimestamp(
                process.create_time(), UTC
            ),
            process_cpu_count=os.process_cpu_count(),
        )

    def read_sessions(self) -> tuple[UserSession, ...]:
        """Read native logged-in user sessions.

        Args:
            None.

        Returns:
            Sessions in native order with UTC start times; unavailable
            terminal, remote host or process identity remains None.
        """
        return tuple(
            UserSession(
                username=user.name,
                terminal=user.terminal,
                host=user.host,
                started_at=datetime.fromtimestamp(user.started, UTC),
                process_id=int(user.pid)
                if (psutil.LINUX or psutil.FREEBSD) and user.pid is not None
                else None,
            )
            for user in psutil.users()
        )

    def read_cpu(self) -> CpuInfo:
        """Read CPU topology, frequencies, cumulative times and counters.

        Args:
            None.

        Returns:
            CPU metadata with frequencies in MHz and CPU times in seconds.
            Unavailable platform-specific values remain None.
        """
        frequencies = psutil.cpu_freq(percpu=True)
        stats = psutil.cpu_stats()
        times = psutil.cpu_times()
        return CpuInfo(
            observed_at=datetime.now(UTC),
            logical_count=psutil.cpu_count(),
            physical_count=psutil.cpu_count(logical=False),
            process_cpu_count=os.process_cpu_count(),
            load_average=psutil.getloadavg() if not psutil.WINDOWS else None,
            frequencies=(
                tuple(
                    CpuFrequency(
                        current_mhz=item.current,
                        minimum_mhz=item.min if item.min > 0 else None,
                        maximum_mhz=item.max if item.max > 0 else None,
                    )
                    for item in frequencies
                )
                if frequencies is not None
                else None
            ),
            times=CpuTimes(
                user_seconds=times.user,
                system_seconds=times.system,
                idle_seconds=times.idle,
                nice_seconds=times.nice if not psutil.WINDOWS else None,
                iowait_seconds=times.iowait if psutil.LINUX else None,
                irq_seconds=times.irq if psutil.LINUX else None,
                softirq_seconds=times.softirq if psutil.LINUX else None,
                steal_seconds=times.steal if psutil.LINUX else None,
                guest_seconds=times.guest if psutil.LINUX else None,
                guest_nice_seconds=times.guest_nice if psutil.LINUX else None,
            ),
            per_cpu_times=tuple(
                CpuTimes(
                    user_seconds=item.user,
                    system_seconds=item.system,
                    idle_seconds=item.idle,
                    nice_seconds=item.nice if not psutil.WINDOWS else None,
                    iowait_seconds=item.iowait if psutil.LINUX else None,
                    irq_seconds=item.irq if psutil.LINUX else None,
                    softirq_seconds=item.softirq if psutil.LINUX else None,
                    steal_seconds=item.steal if psutil.LINUX else None,
                    guest_seconds=item.guest if psutil.LINUX else None,
                    guest_nice_seconds=item.guest_nice
                    if psutil.LINUX
                    else None,
                )
                for item in psutil.cpu_times(percpu=True)
            ),
            context_switches=stats.ctx_switches,
            interrupts=stats.interrupts,
            soft_interrupts=stats.soft_interrupts
            if not psutil.WINDOWS
            else None,
            system_calls=stats.syscalls if not psutil.LINUX else None,
        )

    def read_cpu_usage(self, sample_seconds: float) -> CpuUsage:
        """Read total CPU utilization over a native blocking sample.

        Args:
            sample_seconds: Positive finite sampling interval in seconds.
                This read blocks for the requested interval.

        Returns:
            CPU utilization as a percentage and the requested interval.

        Raises:
            ValueError: The interval is not finite and positive.
        """
        if not isfinite(sample_seconds) or sample_seconds <= 0:
            raise ValueError("sample_seconds must be finite and positive")
        percent = psutil.cpu_percent(interval=sample_seconds)
        return CpuUsage(
            observed_at=datetime.now(UTC),
            sample_seconds=sample_seconds,
            percent=percent,
        )

    def read_core_usage(self, sample_seconds: float) -> CoreCpuUsage:
        """Read per-core CPU utilization over a native blocking sample.

        Args:
            sample_seconds: Positive finite sampling interval in seconds.
                This read blocks for the requested interval.

        Returns:
            Percentages in native CPU order and the requested interval.

        Raises:
            ValueError: The interval is not finite and positive.
        """
        if not isfinite(sample_seconds) or sample_seconds <= 0:
            raise ValueError("sample_seconds must be finite and positive")
        percentages = psutil.cpu_percent(interval=sample_seconds, percpu=True)
        return CoreCpuUsage(
            observed_at=datetime.now(UTC),
            sample_seconds=sample_seconds,
            percentages=tuple(percentages),
        )

    def read_memory(self) -> MemoryInfo:
        """Read native physical memory usage.

        Args:
            None.

        Returns:
            Memory sizes in bytes and utilization as a percentage.
            Unavailable platform-specific values remain None.
        """
        memory = psutil.virtual_memory()
        return MemoryInfo(
            observed_at=datetime.now(UTC),
            total_bytes=memory.total,
            available_bytes=memory.available,
            used_bytes=memory.used,
            free_bytes=memory.free,
            percent=memory.percent,
            active_bytes=memory.active if not psutil.WINDOWS else None,
            inactive_bytes=memory.inactive if not psutil.WINDOWS else None,
            buffers_bytes=memory.buffers if psutil.LINUX else None,
            cached_bytes=memory.cached if psutil.LINUX else None,
            shared_bytes=memory.shared if psutil.LINUX else None,
            slab_bytes=memory.slab if psutil.LINUX else None,
        )

    def read_swap(self) -> SwapInfo:
        """Read native swap usage and cumulative swap I/O.

        Args:
            None.

        Returns:
            Swap sizes and cumulative I/O in bytes, plus utilization percent.
        """
        swap = psutil.swap_memory()
        return SwapInfo(
            observed_at=datetime.now(UTC),
            total_bytes=swap.total,
            used_bytes=swap.used,
            free_bytes=swap.free,
            percent=swap.percent,
            swapped_in_bytes=swap.sin,
            swapped_out_bytes=swap.sout,
        )
