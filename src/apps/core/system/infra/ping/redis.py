from papilio.infra.redis.client import RedisClient
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError


class RedisPing:
    def __init__(self, redis: RedisClient | None) -> None:
        """Bind the application-owned native Redis client.

        Args:
            redis: Configured native client, or None when Redis is disabled.

        Returns:
            None.
        """
        self.redis = redis

    async def ping(self) -> bool:
        """Send the native Redis PING command.

        Args:
            None.

        Returns:
            Native response, or False when the connection is unavailable.
            Unexpected errors and cancellation propagate unchanged.
        """
        result = False
        if self.redis is not None:
            try:
                result = await self.redis.ping()
            except (OSError, RedisConnectionError, RedisTimeoutError):
                result = False
        return result
