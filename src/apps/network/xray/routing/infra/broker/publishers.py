"""Forward committed routing identities through the native Outbox."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.control import RoutingRequested
from .config import BrokerConfig

routing_requested = publisher(
    RoutingRequested,
    subject=BrokerConfig.requested,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.requested,
)
