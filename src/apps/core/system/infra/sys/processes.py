"""Bounded native process enumeration and a separate PID lookup.

Listings contain the first `limit` observable PIDs in ascending order and
report truncation explicitly. Processes may exit while the OS is observed.
Denied attributes retain psutil's None; missing single PIDs return None.
"""

from datetime import UTC, datetime
from itertools import islice
from typing import ClassVar, Protocol, TypedDict, cast

import psutil

from src.apps.core.system.domain.results.processes import (
    ProcessInfo,
    ProcessListing,
)


class IProcessMemory(Protocol):
    @property
    def rss(self) -> int: ...
    @property
    def vms(self) -> int: ...


class IProcessCpuTimes(Protocol):
    @property
    def user(self) -> float: ...
    @property
    def system(self) -> float: ...


class ProcessAttributes(TypedDict):
    pid: int
    ppid: int | None
    name: str | None
    status: str | None
    username: str | None
    create_time: float | None
    num_threads: int | None
    memory_info: IProcessMemory | None
    memory_percent: float | None
    cpu_times: IProcessCpuTimes | None
    nice: int | None


class ProcessReader:
    attributes: ClassVar[tuple[str, ...]] = (
        "pid",
        "ppid",
        "name",
        "status",
        "username",
        "create_time",
        "num_threads",
        "memory_info",
        "memory_percent",
        "cpu_times",
        "nice",
    )

    @staticmethod
    def result_from_attributes(value: ProcessAttributes) -> ProcessInfo:
        """Map the selected native process attributes to a typed result.

        Args:
            value: Selected native attributes; inaccessible values are None.

        Returns:
            Process metadata with UTC timestamps, memory in bytes and CPU
            times in seconds; unavailable attributes remain None.
        """
        memory = value["memory_info"]
        cpu = value["cpu_times"]
        started = value["create_time"]
        return ProcessInfo(
            observed_at=datetime.now(UTC),
            process_id=value["pid"],
            parent_process_id=value["ppid"],
            name=value["name"],
            status=value["status"],
            username=value["username"],
            started_at=datetime.fromtimestamp(started, UTC)
            if started is not None
            else None,
            thread_count=value["num_threads"],
            resident_memory_bytes=memory.rss if memory is not None else None,
            virtual_memory_bytes=memory.vms if memory is not None else None,
            memory_percent=value["memory_percent"],
            cpu_user_seconds=cpu.user if cpu is not None else None,
            cpu_system_seconds=cpu.system if cpu is not None else None,
            priority=value["nice"],
        )

    def read_process(self, process_id: int) -> ProcessInfo | None:
        """Read selected native attributes for one process.

        Args:
            process_id: Positive operating-system process identifier.

        Returns:
            Process metadata, or None if the process no longer exists.
            Inaccessible individual attributes remain None.

        Raises:
            ValueError: The process identifier is not positive.
        """
        if process_id < 1:
            raise ValueError("process_id must be positive")
        result: ProcessInfo | None
        try:
            process = psutil.Process(process_id)
            values = cast(
                ProcessAttributes,
                process.as_dict(attrs=self.attributes, ad_value=None),
            )
        except psutil.NoSuchProcess:
            result = None
        else:
            result = self.result_from_attributes(values)
        return result

    def read_processes(self, *, limit: int) -> ProcessListing:
        """Read a bounded native listing of observable processes.

        Args:
            limit: Positive maximum number of process records to return.

        Returns:
            Processes ordered by PID, with truncation reported explicitly.
            Inaccessible individual attributes remain None.

        Raises:
            ValueError: The limit is not positive.
        """
        if limit < 1:
            raise ValueError("limit must be positive")
        processes = psutil.process_iter(attrs=self.attributes, ad_value=None)
        items = tuple(
            self.result_from_attributes(cast(ProcessAttributes, process.info))
            for process in islice(processes, limit + 1)
        )
        return ProcessListing(
            observed_at=datetime.now(UTC),
            items=items[:limit],
            truncated=len(items) > limit,
        )

    def read_process_count(self) -> int:
        """Read the native number of currently observable process IDs.

        Args:
            None.

        Returns:
            Process count at the time of the native read.
        """
        return len(psutil.pids())
