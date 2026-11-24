"""Typed service contracts for dependency health checks."""

from typing import Protocol

from src.apps.core.system.health.domain.results.pg import PostgresServerTime
from src.apps.core.system.health.domain.results.services import (
    HealthResult,
    PublicHealthResult,
)


class IPublicHealthService(Protocol):
    async def check(self) -> PublicHealthResult:
        """Report public health using PostgreSQL's clock and timezone.

        Args:
            None.

        Returns:
            Status ok/nok, server_time with datetime/timezone or None, and
            attempt duration in milliseconds, without system details.
        """
        ...


class IPostgresHealthService(Protocol):
    async def ping(self) -> HealthResult[bool]:
        """Check PostgreSQL reachability and measure completion time.

        Args:
            None.

        Returns:
            Status ok/nok, boolean availability and attempt milliseconds.
        """
        ...

    async def read_server_time(
        self,
    ) -> HealthResult[PostgresServerTime | None]:
        """Read PostgreSQL-owned time and its reported timezone setting.

        Args:
            None.

        Returns:
            Status ok with PG clock data, or nok with None, and milliseconds.
        """
        ...


class IRedisHealthService(Protocol):
    async def ping(self) -> HealthResult[bool]:
        """Check Redis reachability and measure completion time.

        Args:
            None.

        Returns:
            Status ok/nok, boolean availability and attempt milliseconds.
        """
        ...
