"""Measured system reads through native worker threads."""

from functools import partial

from anyio import to_thread

from src.apps.core.system.app.helpers.measurement import measure
from src.apps.core.system.domain.results.processes import (
    ProcessInfo,
    ProcessListing,
)
from src.apps.core.system.domain.results.services import (
    MeasuredResult,
)
from src.apps.core.system.infra.sys.processes import ProcessReader


class ProcessHealthService:
    def __init__(self, reader: ProcessReader) -> None:
        """Bind the focused reader and native thread execution.

        Args:
            reader: Synchronous system reader.


        Returns:
            None.
        """
        self.reader = reader

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
        result = await measure(
            to_thread.run_sync, self.reader.read_process, process_id
        )
        return result

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
        result = await measure(
            to_thread.run_sync,
            partial(self.reader.read_processes, limit=limit),
        )
        return result

    async def read_process_count(self) -> MeasuredResult[int]:
        """Read the number of observable processes without blocking the loop.

        Args:
            None.

        Returns:
            Native process count and elapsed milliseconds.
        """
        result = await measure(
            to_thread.run_sync, self.reader.read_process_count
        )
        return result
