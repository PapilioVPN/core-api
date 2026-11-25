"""Publish confirmed crypto payments through the native Outbox relay."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.records import PaymentConfirmed
from .config import BrokerConfig

payment_confirmed = publisher(
    PaymentConfirmed,
    subject=BrokerConfig.confirmed,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.confirmed,
)
