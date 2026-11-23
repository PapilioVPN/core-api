"""Insert missing catalog permission scopes by key."""

from collections.abc import Sequence

from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.core.scopes.domain.dtos.records import ScopeCreate
from src.apps.core.scopes.infra.pg.tables import ScopeTable


async def seed_scopes(
    unit: PGUnitOfWork, *, scopes: Sequence[ScopeCreate]
) -> int:
    """Insert the prepared scopes inside the runner's transaction.

    Args:
        unit: Open PostgreSQL unit owned by the runner.
        scopes: Validated scopes for catalog operations.

    Returns:
        Count of newly inserted scopes. Existing keys are preserved.
    """
    if not scopes:
        return 0
    stmt = (
        insert(ScopeTable)
        .values([data.to_row(exclude_unset=False) for data in scopes])
        .on_conflict_do_nothing(index_elements=[col(ScopeTable.key)])
        .returning(col(ScopeTable.id))
    )
    result = await unit.execute(stmt)
    return len(result.scalars().all())
