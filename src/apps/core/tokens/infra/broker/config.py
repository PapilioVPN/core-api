"""Native schedule for expired refresh history."""


class BrokerConfig:
    cleanup_schedule = [
        {
            "schedule_id": "refresh-use-cleanup",
            "interval": 60,
            "kwargs": {"query": {"limit": 100}},
        },
    ]
