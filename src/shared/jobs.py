"""Create the shared native transport configuration for Core jobs."""

from nats.js.api import RetentionPolicy, StreamConfig
from taskiq_nats import PullBasedJetStreamBroker

from src.settings.config import NatsConfig, SchedulerConfig


def create_job_transport(
    nats: NatsConfig, config: SchedulerConfig
) -> PullBasedJetStreamBroker:
    """Build an unconnected transport for publishing or processing jobs."""
    return PullBasedJetStreamBroker(
        nats.servers,
        stream_name=config.stream,
        subject=config.subject,
        durable=config.durable,
        stream_config=StreamConfig(retention=RetentionPolicy.WORK_QUEUE),
        connect_timeout=nats.connect_timeout,
    )
