"""Pure availability policy for measured health probes."""

from src.apps.core.system.domain.results.pg import PostgresServerTime
from src.apps.core.system.domain.results.services import (
    HealthResult,
    MeasuredResult,
)


def ping_result(result: MeasuredResult[bool]) -> HealthResult[bool]:
    """Represent a measured probe as availability data.

    Args:
        result: Original boolean probe and attempt duration.

    Returns:
        Status ok for True or nok for False, retaining value and milliseconds.
    """
    return HealthResult(
        status="ok" if result.value else "nok",
        value=result.value,
        duration_ms=result.duration_ms,
    )


def server_time_result(
    result: MeasuredResult[PostgresServerTime | None],
) -> HealthResult[PostgresServerTime | None]:
    """Represent an available PG clock or an unavailable connection.

    Args:
        result: PG snapshot or None, with measured attempt milliseconds.

    Returns:
        Status ok/nok, original snapshot or None, and attempt duration.
    """
    return HealthResult(
        status="ok" if result.value is not None else "nok",
        value=result.value,
        duration_ms=result.duration_ms,
    )
