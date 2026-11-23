"""Insert missing attribute definitions by key."""

from collections.abc import Sequence

from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.catalog.attributes.domain.dtos.records import AttributeCreate
from src.apps.catalog.attributes.infra.pg.tables import AttributeTable


async def seed_attributes(
    unit: PGUnitOfWork, *, attributes: Sequence[AttributeCreate]
) -> int:
    """Insert the prepared attributes inside the runner's transaction.

    Args:
        unit: Open PostgreSQL unit owned by the runner.
        attributes: Validated attribute definitions with parameter bindings.

    Returns:
        Count of newly inserted definitions. Existing keys are preserved.
    """
    if not attributes:
        return 0
    stmt = (
        insert(AttributeTable)
        .values([data.to_row(exclude_unset=False) for data in attributes])
        .on_conflict_do_nothing(index_elements=[col(AttributeTable.key)])
        .returning(col(AttributeTable.id))
    )
    result = await unit.execute(stmt)
    return len(result.scalars().all())
