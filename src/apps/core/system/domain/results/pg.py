"""PostgreSQL-owned clock information, separate from the API host clock."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PostgresServerTime:
    """A timezone-aware PG instant and its reported TimeZone setting."""

    server_time: datetime
    server_timezone: str
