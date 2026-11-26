"""Compose the native Papilio Tasks broker and module schedules."""

from papilio.core.bootstrap import Bootstrapper
from papilio.providers.base import CoreProvider
from papilio_tasks.apps.schedulers.application import (
    create_beat,
    create_broker,
)
from papilio_tasks.apps.schedulers.backends.nats import JetStreamBroker
from papilio_tasks.apps.schedulers.registry.nats import NatsRegistrar
from papilio_tasks.infra.taskiq.sources.backends.memory import MemorySource
from papilio_tasks.infra.taskiq.sources.base import Source
from papilio_tasks.infra.taskiq.sources.contracts.base import SourceContract
from taskiq import AsyncBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from src.apps.network.nodes.infra.broker.config import (
    BrokerConfig as NodeBrokerConfig,
)
from src.apps.shop.crypto.rates.infra.broker.config import BrokerConfig
from src.bootstrap.providers.infra import infra_providers
from src.settings.config import CoreSettings
from src.shared.jobs import create_job_transport


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
    transport = create_job_transport(nats, settings.scheduler)
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
    sources: list[SourceContract] = [Source(LabelScheduleSource(broker))]
    interval = settings.scheduler.rate_refresh_interval
    if (
        interval is not None
        and settings.redis is not None
        and broker.find_task(BrokerConfig.refresh_task)
    ):
        sources.append(MemorySource([BrokerConfig.refresh_schedule(interval)]))
    probe_interval = settings.node_host.checks.interval_seconds
    if (
        probe_interval is not None
        and settings.node_host.targets
        and broker.find_task(NodeBrokerConfig.probe_task)
    ):
        sources.append(
            MemorySource([NodeBrokerConfig.probe_schedule(probe_interval)])
        )
    beat = create_beat(broker, sources=sources)
    return broker, beat
