"""Stable broker identity and periodic node connection schedule."""

from taskiq import ScheduledTask


class BrokerConfig:
    probe_task = "network.nodes.check_connections.v1"

    @staticmethod
    def probe_schedule(interval: int) -> ScheduledTask:
        """Schedule one due batch with no serialized deployment settings."""
        return ScheduledTask(
            task_name=BrokerConfig.probe_task,
            schedule_id="network-node-probe",
            interval=interval,
            args=[],
            kwargs={},
            labels={},
        )
