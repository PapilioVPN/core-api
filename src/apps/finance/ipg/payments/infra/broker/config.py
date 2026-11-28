"""Own the bounded IPG reconciliation schedule and confirmation subject."""

from faststream.nats import JStream


class BrokerConfig:
    verify_task = "finance.ipg.verify_payments.v1"
    verify_schedule = [
        {
            "schedule_id": "ipg-payment-verification",
            "interval": 60,
            "kwargs": {
                "policy": {
                    "limit": 100,
                    "parallel": 8,
                    "retry_seconds": 600,
                    "window_minutes": 1440,
                }
            },
        },
    ]
    confirmed = "papiliovpn.finance.ipg.payment.confirmed.v1"
    stream = JStream("papiliovpn_finance_ipg_payments", subjects=[confirmed])
