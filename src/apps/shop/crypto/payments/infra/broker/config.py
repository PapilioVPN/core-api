"""Schedule regular batches of outstanding crypto payments."""


class BrokerConfig:
    recheck_schedule = [
        {
            "schedule_id": "crypto-payment-recheck",
            "interval": 300,
            "kwargs": {"query": {"limit": 20, "delay": 300}},
        },
    ]
