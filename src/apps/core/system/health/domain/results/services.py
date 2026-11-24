"""Internal health service results; transport schemas belong to routers."""

from dataclasses import dataclass
from datetime import datetime as DateTime


@dataclass(frozen=True, slots=True)
class MeasuredResult[T]:
    """An operation's value and milliseconds until the result is ready.

    The value preserves source ordering and absence semantics. Duration is
    measured by the app helper, including worker waiting when applicable.
    """

    value: T
    duration_ms: float


@dataclass(frozen=True, slots=True)
class HealthResult[T]:
    """Dependency availability, original typed value and attempt duration."""

    status: str
    value: T
    duration_ms: float


@dataclass(frozen=True, slots=True)
class ServerTime:
    """Timezone-aware PG instant with PostgreSQL's reported TimeZone."""

    datetime: DateTime
    timezone: str


@dataclass(frozen=True, slots=True)
class PublicHealthResult:
    """Public availability, optional server clock and attempt duration.

    status is ok when PG is reachable, otherwise nok with server_time=None.
    duration_ms includes the connection attempt, even when unavailable.
    """

    status: str
    server_time: ServerTime | None
    duration_ms: float
