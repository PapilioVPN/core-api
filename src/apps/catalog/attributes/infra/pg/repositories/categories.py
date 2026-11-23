"""PostgreSQL operations for the owning category-attribute relationship."""

from papilio.infra.db.repositories.backends.postgresql import PGRepository
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import delete, select
from sqlmodel import col

from src.apps.catalog.attributes.domain.models.categories import (
    CategoryAttributeModel,
)
from src.apps.catalog.attributes.domain.results.categories import BindingDetail
from src.apps.catalog.attributes.infra.pg.tables import CategoryAttributeTable


class BindingRepository(PGRepository[CategoryAttributeModel]):
    table = CategoryAttributeTable

    async def save(
        self, data: CategoryAttributeModel
    ) -> CategoryAttributeModel:
        """Store the relationship using its composite identity.

        Args:
            data: Category and attribute identities and assignment settings.

        Returns:
            The persisted binding.
        """
        columns = CategoryAttributeTable.__table__.c
        binding = await self.upsert(
            data,
            conflict_columns=[columns.category_id, columns.attribute_id],
            update_columns=[
                columns.is_required,
                columns.is_filterable,
                columns.is_variant_axis,
                columns.priority,
            ],
        )
        return binding

    async def list(
        self, category_id: int, *, limit: int, offset: int
    ) -> PagedType[BindingDetail]:
        """Read a page of bindings with their attribute definitions.

        Args:
            category_id: Owning category identity.
            limit: Maximum rows.
            offset: Matching rows to skip.

        Returns:
            The total and a page ordered by priority and attribute identity.
        """
        table = CategoryAttributeTable
        stmt = (
            select(table)
            .where(col(table.category_id) == category_id)
            .order_by(col(table.priority), col(table.attribute_id))
        )
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return PagedType(
            items=[
                BindingDetail(
                    category_id=row.category_id,
                    attribute_id=row.attribute_id,
                    is_required=row.is_required,
                    is_filterable=row.is_filterable,
                    is_variant_axis=row.is_variant_axis,
                    priority=row.priority,
                    attribute=row.attribute,
                )
                for row in page.items
            ],
            total_items=page.total_items,
        )

    async def remove_from(
        self, category_id: int, attribute_id: int
    ) -> CategoryAttributeModel | None:
        """Delete the relationship identified by both of its owners.

        Args:
            category_id: Owning category identity.
            attribute_id: Assigned attribute identity.

        Returns:
            The removed binding, or None if the pair was absent.
        """
        table = self.table
        stmt = (
            delete(table)
            .where(
                col(table.category_id) == category_id,
                col(table.attribute_id) == attribute_id,
            )
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        return result.scalar_one_or_none()
