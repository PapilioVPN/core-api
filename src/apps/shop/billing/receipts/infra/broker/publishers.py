"""Register the typed receipt publications with Events and Outbox."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.records import ReceiptCreated
from .config import BrokerConfig

receipt_created = publisher(
    ReceiptCreated,
    subject=BrokerConfig.created,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.created,
)
