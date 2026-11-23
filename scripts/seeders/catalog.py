"""Insert missing starter catalog definitions by their stable keys."""

from dataclasses import dataclass

from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.catalog.attributes.domain.dtos.records import AttributeCreate
from src.apps.catalog.attributes.domain.enums.records import (
    AttributeType,
    ParamKey,
)
from src.apps.catalog.attributes.infra.pg.tables import (
    AttributeTable,
    CategoryAttributeTable,
)
from src.apps.catalog.categories.domain.dtos.records import CategoryCreate
from src.apps.catalog.categories.infra.pg.tables import CategoryTable
from src.apps.core.scopes.domain.dtos.records import ScopeCreate
from src.apps.core.scopes.infra.pg.tables import ScopeTable

CATEGORY = CategoryCreate(slug="subscriptions", title="Subscriptions")
SCOPE = ScopeCreate(key="catalog", title="Catalog")
ATTRIBUTES = (
    AttributeCreate(
        key="duration_days",
        label="Duration (days)",
        type=AttributeType.INT,
        param_key=ParamKey.DURATION_DAYS,
    ),
    AttributeCreate(
        key="quota_bytes",
        label="Quota (bytes)",
        type=AttributeType.INT,
        param_key=ParamKey.QUOTA_BYTES,
    ),
)


@dataclass(frozen=True, slots=True)
class CatalogSeed:
    scopes: int
    categories: int
    attributes: int
    bindings: int


async def seed_catalog(unit: PGUnitOfWork) -> CatalogSeed:
    """Insert defaults in dependency order inside the caller's transaction.

    Args:
        unit: Open PostgreSQL unit with the catalog schema applied.

    Returns:
        Counts of newly inserted scopes, categories, attributes and bindings.
        Existing fields and bindings are preserved.
    """
    stmt = (
        insert(ScopeTable)
        .values(SCOPE.to_row(exclude_unset=False))
        .on_conflict_do_nothing(index_elements=[col(ScopeTable.key)])
        .returning(col(ScopeTable.id))
    )
    result = await unit.execute(stmt)
    scopes = len(result.scalars().all())
    stmt = (
        insert(CategoryTable)
        .values(CATEGORY.to_row(exclude_unset=False))
        .on_conflict_do_nothing(index_elements=[col(CategoryTable.slug)])
        .returning(col(CategoryTable.id))
    )
    result = await unit.execute(stmt)
    categories = len(result.scalars().all())
    stmt = (
        insert(AttributeTable)
        .values([data.to_row(exclude_unset=False) for data in ATTRIBUTES])
        .on_conflict_do_nothing(index_elements=[col(AttributeTable.key)])
        .returning(col(AttributeTable.id))
    )
    result = await unit.execute(stmt)
    attributes = len(result.scalars().all())

    query = select(col(CategoryTable.id)).where(
        col(CategoryTable.slug) == CATEGORY.slug
    )
    result = await unit.execute(query)
    category_id = result.scalar_one()
    query = select(col(AttributeTable.key), col(AttributeTable.id)).where(
        col(AttributeTable.key).in_([data.key for data in ATTRIBUTES])
    )
    result = await unit.execute(query)
    ids = dict(result.tuples().all())

    stmt = (
        insert(CategoryAttributeTable)
        .values(
            [
                {
                    "category_id": category_id,
                    "attribute_id": ids[data.key],
                    "is_required": True,
                    "is_filterable": True,
                    "is_variant_axis": True,
                    "priority": priority,
                }
                for priority, data in enumerate(ATTRIBUTES)
            ]
        )
        .on_conflict_do_nothing(
            index_elements=[
                col(CategoryAttributeTable.category_id),
                col(CategoryAttributeTable.attribute_id),
            ]
        )
        .returning(col(CategoryAttributeTable.attribute_id))
    )
    result = await unit.execute(stmt)
    return CatalogSeed(
        scopes=scopes,
        categories=categories,
        attributes=attributes,
        bindings=len(result.scalars().all()),
    )
