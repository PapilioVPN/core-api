"""Publish a manual refresh with Taskiq's native producer."""

from taskiq import AsyncBroker
from taskiq.exceptions import SendTaskError
from taskiq.kicker import AsyncKicker

from ...domain.models.records import Rate
from ...domain.results.records import RateFailure
from .tasks import refresh_rate


class RateRefreshPublisher:
    def __init__(self, broker: AsyncBroker) -> None:
        """Borrow the HTTP application's job transport."""
        self.broker = broker

    async def enqueue(self) -> str | RateFailure:
        """Queue a rate refresh with no serialized arguments.

        Returns:
            The native task ID, or a queue failure.
        """
        kicker = AsyncKicker[[], Rate | RateFailure](
            refresh_rate.name, self.broker, {}
        )
        try:
            task = await kicker.kiq()
        except SendTaskError:
            result = RateFailure.QUEUE_UNAVAILABLE
        else:
            result = task.task_id
        return result
