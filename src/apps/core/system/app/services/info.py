"""Public health reports the measured PostgreSQL clock only."""

from src.apps.core.system.app.interfaces.health import (
    IPostgresHealthService,
)
from src.apps.core.system.domain.results.services import (
    PublicHealthResult,
    ServerTime,
)


class PublicHealthService:
    def __init__(self, postgres: IPostgresHealthService) -> None:
        """Bind the explicit PostgreSQL app contract.

        Args:
            postgres: Service returning the authoritative measured PG clock.

        Returns:
            None.
        """
        self.postgres = postgres

    async def check(self) -> PublicHealthResult:
        """Report PG availability with its optional nested server clock.

        Args:
            None.

        Returns:
            Status ok with a server clock, or nok with server_time=None.
            Both include attempt milliseconds. Unexpected errors propagate.
        """
        measured = await self.postgres.read_server_time()
        server_time: ServerTime | None = None
        if measured.value is not None:
            server_time = ServerTime(
                datetime=measured.value.server_time,
                timezone=measured.value.server_timezone,
            )
        return PublicHealthResult(
            status=measured.status,
            server_time=server_time,
            duration_ms=measured.duration_ms,
        )
