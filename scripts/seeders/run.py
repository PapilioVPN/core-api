"""Run the initial data seeds against the configured, migrated database."""

from asyncio import run

from papilio.core.config import DatabaseConfig, get_settings
from papilio.infra.db.connection import DBConnection
from papilio.infra.db.uow import PGUnitOfWork

from scripts.seeders.catalog import CatalogSeed, seed_catalog
from src.settings.config import CoreSettings


async def seed(config: DatabaseConfig) -> CatalogSeed:
    """Run the catalog seeds in a single native PostgreSQL transaction.

    Args:
        config: Database connection and pool settings.

    Returns:
        Committed insert counts. Failure rolls back the seed.
    """
    database = DBConnection(
        dsn=config.dsn,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_recycle=config.pool_recycle,
        uow_factory=PGUnitOfWork,
    )
    try:
        async with database.uow() as unit, unit.transaction():
            result = await seed_catalog(unit)
    finally:
        await database.dispose()
    return result


def main() -> None:
    """Read the selected runtime settings and report committed seed counts."""
    config = get_settings(CoreSettings).db
    if config is None:
        raise SystemExit("Database settings are required")
    result = run(seed(config))
    print(
        f"Catalog seed committed. Added {result.scopes} scopes, "
        f"{result.categories} categories, {result.attributes} attributes, "
        f"{result.bindings} bindings."
    )


if __name__ == "__main__":
    main()
