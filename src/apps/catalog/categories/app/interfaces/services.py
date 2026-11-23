"""Category identity contract for other catalog capabilities."""

from typing import Protocol

from src.apps.catalog.categories.domain.models.records import CategoryModel


class ICategoryService(Protocol):
    async def get_by_id(self, id: int) -> CategoryModel:
        """Get an existing category or raise a native not-found error."""
        ...
