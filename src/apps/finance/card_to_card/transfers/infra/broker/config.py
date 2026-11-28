"""Own the JetStream identity for recorded bank transfers."""

from faststream.nats import JStream


class BrokerConfig:
    created = "papiliovpn.finance.card_to_card.transfer.created.v1"
    stream = JStream("papiliovpn_finance_card_transfers", subjects=[created])
