"""Forward committed bank transfer identities through the native Outbox."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.records import TransferCreated
from .config import BrokerConfig

transfer_created = publisher(
    TransferCreated,
    subject=BrokerConfig.created,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.created,
)
