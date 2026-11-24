"""Compose the native Events application from selected modules."""

from faststream.nats import NatsBroker as NativeNatsBroker
from papilio.core.bootstrap import Bootstrapper
from papilio.providers.base import CoreProvider
from papilio_tasks.apps.events.application import Application, create_app
from papilio_tasks.apps.events.registry.jetstream import JetRegistrar
from papilio_tasks.infra.faststream.brokers.backends.nats import NatsBroker

from src.apps.shop.billing.ocr_requests.tasks.subscribers.receipts import (
    create_router as ocr_router,
)
from src.bootstrap.providers.infra import infra_providers
from src.settings.config import CoreSettings


def registrar(settings: CoreSettings) -> JetRegistrar:
    """Configure native JetStream without opening NATS."""
    nats = settings.nats
    if nats is None:
        raise ValueError("Configure nats.servers to start events")
    broker = NativeNatsBroker(
        nats.servers,
        connect_timeout=nats.connect_timeout,
        graceful_timeout=nats.graceful_timeout,
    )
    return JetRegistrar(NatsBroker(broker))


def create_events_producer(settings: CoreSettings) -> Application:
    """Bind the relay's target publishers without starting subscribers."""
    app = create_app(
        registrar=registrar(settings), publishers=settings.app.modules
    )
    return app


def create_events(settings: CoreSettings) -> Application:
    """Bind native event discovery without opening NATS."""
    discover = Bootstrapper(
        settings.app.modules, tables_path=settings.app.tables_path
    )
    app = create_app(
        registrar=registrar(settings),
        providers=[
            CoreProvider(settings),
            *infra_providers(settings),
            *discover.boot_providers(),
        ],
        publishers=settings.app.modules,
        subscribers=settings.app.modules,
        routers=[ocr_router()] if settings.ocr is not None else [],
    )
    return app
