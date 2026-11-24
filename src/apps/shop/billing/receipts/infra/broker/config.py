"""JetStream subject for receipt creation."""

from faststream.nats import JStream


class BrokerConfig:
    created = "papiliovpn.shop.receipts.created"
    stream = JStream("papiliovpn_shop_receipts", subjects=[created])
