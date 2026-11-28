"""Insert missing card prefixes using stored Iranian bank identities."""

from collections.abc import Sequence
from itertools import batched

from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from scripts.seeders.banking.data import BankSeed
from src.apps.finance.banking.banks.infra.pg.tables import BankTable
from src.apps.finance.banking.card_prefixes.infra.pg.tables import (
    CardPrefixTable,
)


async def seed_card_prefixes(
    unit: PGUnitOfWork, *, banks: Sequence[BankSeed]
) -> int:
    """Resolve bank codes once and insert prefixes in bounded native sets.

    Args:
        unit: Open PostgreSQL unit after the bank seed.
        banks: Offline validated bank references with exact prefix strings.

    Returns:
        Number of newly inserted prefixes. Existing ownership and activity
        are preserved; no bank or prefix identity is hardcoded.
    """
    stmt = select(col(BankTable.code), col(BankTable.id)).where(
        col(BankTable.code).in_(bank.code for bank in banks)
    )
    result = await unit.execute(stmt)
    bank_ids = dict(result.tuples().all())
    rows = (
        {
            "bank_id": bank_ids[bank.code],
            "prefix": prefix,
            "is_active": bank.is_active,
        }
        for bank in banks
        for prefix in bank.prefixes
    )
    inserted = 0
    for batch in batched(rows, 500):
        stmt = (
            insert(CardPrefixTable)
            .values(list(batch))
            .on_conflict_do_nothing(
                index_elements=[col(CardPrefixTable.prefix)]
            )
            .returning(col(CardPrefixTable.id))
        )
        result = await unit.execute(stmt)
        inserted += len(result.scalars().all())
    return inserted
