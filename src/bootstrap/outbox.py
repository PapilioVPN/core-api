"""Compose native transactional event publication."""

from faststream_outbox import OutboxBroker, make_dlq_table, make_outbox_table
from papilio_tasks.apps.outbox import Outbox
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine

from src.settings.config import CoreSettings

metadata = MetaData()
pending = make_outbox_table(metadata, table_name="event_outbox")
dead_letters = make_dlq_table(metadata, table_name="event_outbox_dlq")


def create_outbox(
    settings: CoreSettings, *, engine: AsyncEngine | None = None
) -> Outbox:
    """Bind discovered publishers to the native queue without opening I/O."""
    runtime = Outbox(
        OutboxBroker(engine, outbox_table=pending, dlq_table=dead_letters),
        modules=settings.app.modules,
    )
    return runtime
