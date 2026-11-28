"""Insert missing Iranian banks without changing existing bank fields."""

from collections.abc import Sequence
from itertools import batched

from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from scripts.seeders.banking.data import BankSeed
from src.apps.finance.banking.banks.infra.pg.tables import BankTable


async def seed_banks(unit: PGUnitOfWork, *, banks: Sequence[BankSeed]) -> int:
    """Insert missing Iranian bank codes in bounded batches.

    Args:
        unit: Open PostgreSQL unit.
        banks: Offline validated bank references.

    Returns:
        Number of newly inserted banks. Existing fields remain unchanged.
    """
    inserted = 0
    for batch in batched(banks, 500):
        stmt = (
            insert(BankTable)
            .values(
                [
                    {
                        "code": bank.code,
                        "title": bank.title,
                        "icon_url": bank.icon_url,
                        "is_active": bank.is_active,
                        "priority": bank.priority,
                    }
                    for bank in batch
                ]
            )
            .on_conflict_do_nothing(index_elements=[col(BankTable.code)])
            .returning(col(BankTable.id))
        )
        result = await unit.execute(stmt)
        inserted += len(result.scalars().all())
    return inserted
