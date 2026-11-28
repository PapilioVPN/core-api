"""Own card payment publication and subscription identities."""

from faststream.nats import JStream


class BrokerConfig:
    confirmed = "papiliovpn.finance.card_to_card.payment.confirmed.v1"
    rejected = "papiliovpn.finance.card_to_card.payment.rejected.v1"
    stream = JStream(
        "papiliovpn_finance_card_payments", subjects=[confirmed, rejected]
    )
    transfer_durable = "papiliovpn_finance_card_confirm"
