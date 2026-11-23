"""Process metadata without command lines, environment or file contents."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput


class ProcessOutput(BaseOutput):
    observed_at: datetime
    process_id: int
    parent_process_id: int | None
    name: str | None
    status: str | None
    username: str | None
    started_at: datetime | None
    thread_count: int | None
    resident_memory_bytes: int | None
    virtual_memory_bytes: int | None
    memory_percent: float | None
    cpu_user_seconds: float | None
    cpu_system_seconds: float | None
    priority: int | None


class ProcessListingOutput(BaseOutput):
    observed_at: datetime
    items: tuple[ProcessOutput, ...]
    truncated: bool
