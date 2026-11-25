"""Publish a manual refresh with Taskiq's native producer."""

from taskiq import AsyncBroker
from taskiq.exceptions import SendTaskError
from taskiq.kicker import AsyncKicker

from ...domain.errors import RefreshUnavailable
from .tasks import refresh_rate


class RateRefreshPublisher:
    def __init__(self, broker: AsyncBroker) -> None:
        """Borrow the HTTP application's job transport."""
        self.broker = broker

    async def enqueue(self) -> str:
        """Queue a rate refresh with no serialized arguments.

        Returns:
            The native ID after JetStream acknowledges the enqueue.

        Raises:
            RefreshUnavailable: The broker did not confirm publication.
        """
        kicker = AsyncKicker[[], None](refresh_rate.name, self.broker, {})
        try:
            task = await kicker.kiq()
        except SendTaskError as error:
            raise RefreshUnavailable() from error
        return task.task_id
