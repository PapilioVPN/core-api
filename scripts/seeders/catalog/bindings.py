"""Assign the starter attributes to their category using stored identities."""

from collections.abc import Sequence

from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.catalog.attributes.infra.pg.tables import (
    AttributeTable,
    CategoryAttributeTable,
)
from src.apps.catalog.categories.infra.pg.tables import CategoryTable


async def seed_bindings(
    unit: PGUnitOfWork, *, slug: str, keys: Sequence[str]
) -> int:
    """Insert missing assignments inside the runner's transaction.

    Args:
        unit: Open PostgreSQL unit after the category and attribute seeds.
        slug: Stable category slug.
        keys: Attribute keys in display order.

    Returns:
        Count of newly inserted bindings. Existing assignments are preserved.
    """
    if not keys:
        return 0
    stmt = select(col(CategoryTable.id)).where(col(CategoryTable.slug) == slug)
    result = await unit.execute(stmt)
    category_id = result.scalar_one()
    stmt = select(col(AttributeTable.key), col(AttributeTable.id)).where(
        col(AttributeTable.key).in_(keys)
    )
    result = await unit.execute(stmt)
    ids = dict(result.tuples().all())

    binding = CategoryAttributeTable
    stmt = (
        insert(binding)
        .values(
            [
                {
                    "category_id": category_id,
                    "attribute_id": ids[key],
                    "is_required": True,
                    "is_filterable": True,
                    "is_variant_axis": True,
                    "priority": priority,
                }
                for priority, key in enumerate(keys)
            ]
        )
        .on_conflict_do_nothing(
            index_elements=[
                col(binding.category_id),
                col(binding.attribute_id),
            ]
        )
        .returning(col(binding.attribute_id))
    )
    result = await unit.execute(stmt)
    return len(result.scalars().all())
