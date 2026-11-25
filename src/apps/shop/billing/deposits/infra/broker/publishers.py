"""Register bank reports in Events and the native Outbox."""

from papilio_tasks.apps.events.publishers.jetstream import publisher

from ...domain.events.records import DepositReceived
from .config import BrokerConfig

deposit_received = publisher(
    DepositReceived,
    subject=BrokerConfig.received,
    stream=BrokerConfig.stream,
    outbox_key=BrokerConfig.received,
)
