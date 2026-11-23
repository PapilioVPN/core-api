"""Compose the native Papilio Tasks broker and module schedules."""

from nats.js.api import RetentionPolicy, StreamConfig
from papilio.core.bootstrap import Bootstrapper
from papilio.providers.base import CoreProvider
from papilio_tasks.apps.schedulers.application import (
    create_beat,
    create_broker,
)
from papilio_tasks.apps.schedulers.backends.nats import JetStreamBroker
from papilio_tasks.apps.schedulers.registry.nats import NatsRegistrar
from papilio_tasks.infra.taskiq.sources.base import Source
from taskiq import AsyncBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_nats import PullBasedJetStreamBroker

from src.bootstrap.providers.infra import infra_providers
from src.settings.config import CoreSettings


def create_scheduler(
    settings: CoreSettings,
) -> tuple[AsyncBroker, TaskiqScheduler]:
    """Bind configured NATS transport and native job discovery.

    Args:
        settings: Selected app roots, access to PostgreSQL and NATS settings.

    Returns:
        Native worker broker and beat without opening network connections.
    """
    nats = settings.nats
    if nats is None:
        raise ValueError("Configure nats.servers to start the scheduler")
    config = settings.scheduler
    transport = PullBasedJetStreamBroker(
        nats.servers,
        stream_name=config.stream,
        subject=config.subject,
        durable=config.durable,
        stream_config=StreamConfig(retention=RetentionPolicy.WORK_QUEUE),
        connect_timeout=nats.connect_timeout,
    )
    discovery = Bootstrapper(
        settings.app.modules, tables_path=settings.app.tables_path
    )
    broker = create_broker(
        registrar=NatsRegistrar(JetStreamBroker(transport)),
        providers=[
            CoreProvider(settings),
            *infra_providers(settings),
            *discovery.boot_providers(),
        ],
        modules=settings.app.modules,
    )
    beat = create_beat(broker, sources=[Source(LabelScheduleSource(broker))])
    return broker, beat
