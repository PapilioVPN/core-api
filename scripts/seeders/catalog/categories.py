"""Insert missing catalog categories by slug."""

from collections.abc import Sequence

from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.catalog.categories.domain.dtos.records import CategoryCreate
from src.apps.catalog.categories.infra.pg.tables import CategoryTable


async def seed_categories(
    unit: PGUnitOfWork, *, categories: Sequence[CategoryCreate]
) -> int:
    """Insert the prepared categories inside the runner's transaction.

    Args:
        unit: Open PostgreSQL unit owned by the runner.
        categories: Validated catalog categories.

    Returns:
        Count of newly inserted categories. Existing slugs are preserved.
    """
    if not categories:
        return 0
    stmt = (
        insert(CategoryTable)
        .values([data.to_row(exclude_unset=False) for data in categories])
        .on_conflict_do_nothing(index_elements=[col(CategoryTable.slug)])
        .returning(col(CategoryTable.id))
    )
    result = await unit.execute(stmt)
    return len(result.scalars().all())
