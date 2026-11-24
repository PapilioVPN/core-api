"""JetStream subjects for manual payment decisions."""

from faststream.nats import JStream


class BrokerConfig:
    confirmed = "papiliovpn.shop.payments.confirmed"
    rejected = "papiliovpn.shop.payments.rejected"
    stream = JStream(
        "papiliovpn_shop_payments", subjects=[confirmed, rejected]
    )
