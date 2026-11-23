"""Run native Alembic migrations using Papilio's table discovery."""

from asyncio import run

from alembic import context
from papilio.core.bootstrap import get_bootstrapper
from papilio.core.config import get_settings
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

# Keep retired tables from published revisions out of schema comparisons.
RETIRED_TABLES = {
    "tbl_attributes",
    "tbl_categories",
    "tbl_category_attributes",
    "tbl_payments_legacy",
    "tbl_receipts",
    "tbl_volume_ranges_legacy",
}

get_bootstrapper().boot_sqlmodels()
database = get_settings().db
if database is None:
    raise ValueError("Database settings are required")


def migrate(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=SQLModel.metadata,
        include_name=lambda name, type_, _: (
            type_ != "table"
            or name not in RETIRED_TABLES
            or name in SQLModel.metadata.tables
        ),
    )
    with context.begin_transaction():
        context.run_migrations()


async def online(dsn: str) -> None:
    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(migrate)
    finally:
        await engine.dispose()


url = context.config.get_main_option("sqlalchemy.url") or database.dsn
if context.is_offline_mode():
    context.configure(
        url=url,
        target_metadata=SQLModel.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run(online(url))
