"""Publish committed Xray start requests through the native Outbox."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.start import XrayStartRequested
from .config import BrokerConfig

start_requested = publisher(
    XrayStartRequested,
    subject=BrokerConfig.start_requested,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.start_requested,
)
