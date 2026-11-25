"""Schedule bounded checks of outstanding Plisio payments."""


class BrokerConfig:
    recheck_schedule = [
        {
            "schedule_id": "crypto-payment-recheck",
            "interval": 300,
            "kwargs": {
                "query": {"limit": 100, "delay": 300, "concurrency": 8}
            },
        },
    ]
