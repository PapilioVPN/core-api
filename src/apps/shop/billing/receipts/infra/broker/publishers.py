"""Register the typed receipt publications with Events and Outbox."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.review import (
    ReceiptApproved,
    ReceiptCreated,
    ReceiptRejected,
)
from .config import BrokerConfig

receipt_created = publisher(
    ReceiptCreated,
    subject=BrokerConfig.created,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.created,
)
receipt_approved = publisher(
    ReceiptApproved,
    subject=BrokerConfig.approved,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.approved,
)
receipt_rejected = publisher(
    ReceiptRejected,
    subject=BrokerConfig.rejected,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.rejected,
)
