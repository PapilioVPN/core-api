"""JetStream identities for received bank reports."""

from faststream.nats import JStream


class BrokerConfig:
    received = "papiliovpn.shop.deposits.received"
    match_durable = "papiliovpn_deposit_match"
    stream = JStream("papiliovpn_shop_deposits", subjects=[received])
