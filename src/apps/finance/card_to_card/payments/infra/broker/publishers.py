"""Relay committed card payment decisions."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.records import PaymentConfirmed, PaymentRejected
from .config import BrokerConfig

payment_confirmed = publisher(
    PaymentConfirmed,
    subject=BrokerConfig.confirmed,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.confirmed,
)

payment_rejected = publisher(
    PaymentRejected,
    subject=BrokerConfig.rejected,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.rejected,
)
