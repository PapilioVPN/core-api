"""Log admissions and the lifetime of authorized log observations."""

from collections.abc import AsyncIterator
from dataclasses import dataclass

from ..enums.logs import LogStreamEnd


@dataclass(frozen=True, slots=True)
class LogStream[Entry]:
    entries: AsyncIterator[Entry | LogStreamEnd] | None = None
    end: LogStreamEnd | None = None
