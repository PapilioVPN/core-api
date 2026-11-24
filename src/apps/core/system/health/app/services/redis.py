"""Measured Redis health operations on the client's owning loop."""

from src.apps.core.system.health.app.helpers.measurement import measure
from src.apps.core.system.health.app.helpers.ping import ping_result
from src.apps.core.system.health.domain.results.services import HealthResult
from src.apps.core.system.health.infra.ping.redis import RedisPing


class RedisHealthService:
    def __init__(self, redis: RedisPing) -> None:
        """Bind the native async probe.

        Args:
            redis: Application-owned Redis probe.

        Returns:
            None.
        """
        self.redis = redis

    async def ping(self) -> HealthResult[bool]:
        """Measure the probe and report availability.

        Args:
            None.

        Returns:
            Status ok/nok, boolean availability and attempt milliseconds.
        """
        measured = await measure(self.redis.ping)
        result = ping_result(measured)
        return result
