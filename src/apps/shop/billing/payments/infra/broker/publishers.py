"""Typed publications for finalized payments."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.records import PaymentEvent
from .config import BrokerConfig

payment_confirmed = publisher(
    PaymentEvent,
    subject=BrokerConfig.confirmed,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.confirmed,
)
payment_rejected = publisher(
    PaymentEvent,
    subject=BrokerConfig.rejected,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.rejected,
)
