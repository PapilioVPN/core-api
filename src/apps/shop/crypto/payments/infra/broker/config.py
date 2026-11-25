"""Declare cryptocurrency payment jobs and events."""

from faststream.nats import JStream


class BrokerConfig:
    confirmed = "papiliovpn.shop.crypto.payments.confirmed"
    stream = JStream("papiliovpn_shop_crypto_payments", subjects=[confirmed])
    recheck_schedule = [
        {
            "schedule_id": "crypto-payment-recheck",
            "interval": 300,
            "kwargs": {
                "query": {"limit": 100, "delay": 300, "concurrency": 8}
            },
        },
    ]
