"""JetStream subjects for receipt lifecycle facts."""

from faststream.nats import JStream


class BrokerConfig:
    created = "papiliovpn.shop.receipts.created"
    approved = "papiliovpn.shop.receipts.approved"
    rejected = "papiliovpn.shop.receipts.rejected"
    stream = JStream(
        "papiliovpn_shop_receipts", subjects=[created, approved, rejected]
    )
