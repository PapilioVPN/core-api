"""Run all seeds or selected groups/modules with native DB settings."""

import argparse
import asyncio
from dataclasses import dataclass

from papilio.core.config import DatabaseConfig, get_settings
from papilio.infra.db.connection import DBConnection
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.db.uow import PGUnitOfWork

from scripts.seeders.registry import Seed, registered_seeds, select_seeds


@dataclass(slots=True)
class SeedResult:
    key: str
    inserted: int


@transactional
async def execute_seeds(
    unit: PGUnitOfWork, seeds: tuple[Seed, ...]
) -> list[SeedResult]:
    """Execute the prepared plan sequentially inside one native transaction.

    Args:
        unit: Open PostgreSQL unit bound to the current execution.
        seeds: Ordered plan, prepared and validated before async execution.

    Returns:
        Per-module insert counts. Any failure rolls back the entire plan.
    """
    results: list[SeedResult] = []
    for seed in seeds:
        inserted = await seed.execute(unit)
        results.append(SeedResult(seed.key, inserted))
    return results


async def run_seeds(
    config: DatabaseConfig, seeds: tuple[Seed, ...]
) -> list[SeedResult]:
    """Own one connection lifecycle for the selected standalone seed run.

    Args:
        config: Native configuration of the explicitly selected database.
        seeds: Prepared plan including ordered prerequisites.

    Returns:
        Per-module counts after successful commit and connection cleanup.
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
        async with database.uow() as unit:
            results = await execute_seeds(unit, seeds)
    finally:
        await database.dispose()
    return results


def main() -> None:
    """Select seeds, validate offline inputs and report committed counts."""
    parser = argparse.ArgumentParser(
        description="Seed all modules or selected groups/module keys.",
        epilog=(
            "Use banking for both seeds, or banking.card_prefixes "
            "for the module with prerequisites. Run migrations first. "
            "PAPILIO_CONFIG "
            "selects configuration; default: config.yml."
        ),
    )
    parser.add_argument("targets", nargs="*", help="Group or module keys")
    parser.add_argument(
        "--list", action="store_true", help="List seeds and prerequisites"
    )
    args = parser.parse_args()
    try:
        seeds = select_seeds(registered_seeds(), args.targets)
    except ValueError as error:
        parser.error(str(error))
    if args.list:
        for seed in seeds:
            dependencies = ", ".join(seed.requires) or "none"
            print(f"{seed.key} (requires: {dependencies})")
        return
    config = get_settings().db
    if config is None:
        parser.error("The selected configuration has no db section")
    results = asyncio.run(run_seeds(config, seeds))
    print("Seed committed. Inserted:")
    for result in results:
        print(f"  {result.key}: {result.inserted}")


if __name__ == "__main__":
    main()
