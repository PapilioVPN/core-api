"""Own the hosted card payment publication identity."""

from faststream.nats import JStream


class BrokerConfig:
    confirmed = "papiliovpn.finance.card_gateway.payment.confirmed.v1"
    stream = JStream(
        "papiliovpn_finance_card_gateway_payments", subjects=[confirmed]
    )
