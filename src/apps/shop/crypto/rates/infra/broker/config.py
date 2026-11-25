"""Stable broker identity and native schedule for rate refresh."""

from taskiq import ScheduledTask


class BrokerConfig:
    refresh_task = "shop.crypto.rates.refresh.v1"

    @staticmethod
    def refresh_schedule(interval: int) -> ScheduledTask:
        """Define one repeating refresh with no serialized arguments."""
        return ScheduledTask(
            task_name=BrokerConfig.refresh_task,
            schedule_id="crypto-rate-refresh",
            interval=interval,
            args=[],
            kwargs={},
            labels={},
        )
