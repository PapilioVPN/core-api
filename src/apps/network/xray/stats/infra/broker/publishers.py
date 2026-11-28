"""Forward committed traffic reset identities through the native Outbox."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.reset import TrafficResetRequested
from .config import BrokerConfig

traffic_reset_requested = publisher(
    TrafficResetRequested,
    subject=BrokerConfig.requested,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.requested,
)
