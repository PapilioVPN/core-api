"""Measured PostgreSQL health operations on the client's owning loop."""

from src.apps.core.system.app.helpers.measurement import measure
from src.apps.core.system.app.helpers.ping import (
    ping_result,
    server_time_result,
)
from src.apps.core.system.domain.results.pg import PostgresServerTime
from src.apps.core.system.domain.results.services import (
    HealthResult,
)
from src.apps.core.system.infra.ping.pg import PostgresPing


class PostgresHealthService:
    def __init__(self, postgres: PostgresPing) -> None:
        """Bind the PostgreSQL reader.

        Args:
            postgres: Native async reader owned by the application.

        Returns:
            None.
        """
        self.postgres = postgres

    async def ping(self) -> HealthResult[bool]:
        """Measure a PostgreSQL probe without moving its client to a worker.

        Args:
            None.

        Returns:
            Status ok/nok, boolean availability and attempt milliseconds.
        """
        measured = await measure(self.postgres.ping)
        result = ping_result(measured)
        return result

    async def read_server_time(
        self,
    ) -> HealthResult[PostgresServerTime | None]:
        """Measure the focused PG time/timezone read on its owning loop.

        Args:
            None.

        Returns:
            Status ok with PG clock data, or nok with None, and milliseconds.
            Unexpected errors and cancellation propagate unchanged.
        """
        measured = await measure(self.postgres.read_server_time)
        result = server_time_result(measured)
        return result
