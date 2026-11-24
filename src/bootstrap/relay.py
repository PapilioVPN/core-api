"""Compose the native Outbox relay and its JetStream producer."""

from papilio_tasks.apps.outbox.application import RelayApplication
from sqlalchemy.ext.asyncio import create_async_engine

from src.bootstrap.events import create_events_producer
from src.bootstrap.outbox import create_outbox
from src.settings.config import CoreSettings


def create_relay_app(settings: CoreSettings) -> RelayApplication:
    """Bind native forwarding and release its engine on shutdown."""
    db = settings.db
    if db is None:
        raise ValueError("Configure db to start the outbox relay")
    producer = create_events_producer(settings)
    engine = create_async_engine(
        db.dsn,
        pool_size=db.pool_size,
        max_overflow=db.max_overflow,
        pool_timeout=db.pool_timeout,
        pool_recycle=db.pool_recycle,
    )
    runtime = create_outbox(settings, engine=engine)
    app = runtime.create_relay(producers=[producer])
    app.on_startup(producer.start)
    app.after_shutdown(engine.dispose)
    return app
