"""Native schedule for expired administrator sessions."""


class BrokerConfig:
    cleanup_schedule = [
        {"schedule_id": "admin-sessions-cleanup", "interval": 60},
    ]
