"""Category writes and panel reads through native Papilio services."""

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.catalog.categories.domain.dtos.records import (
    CategoryCreate,
    CategoryList,
    CategoryUpdate,
)
from src.apps.catalog.categories.domain.models.records import CategoryModel
from src.apps.catalog.categories.infra.pg.repositories.records import (
    CategoryRepository,
)


class CategoryService(IDChecks[CategoryModel]):
    entity = "Category"

    def __init__(self, repo: CategoryRepository) -> None:
        """Bind the request's category repository."""
        self.repo = repo

    @handle_conflicts
    @transactional
    async def create(self, data: CategoryCreate) -> CategoryModel:
        """Create a category with a stable slug.

        Args:
            data: Validated category fields.

        Returns:
            The created category.

        Raises:
            ConflictException: The slug is already registered.
        """
        category = await self.repo.create(
            CategoryModel(
                slug=data.slug,
                title=data.title,
                description=data.description,
                priority=data.priority,
                is_active=data.is_active,
            )
        )
        return category

    async def get_by_id(self, id: int) -> CategoryModel:
        """Read one category.

        Args:
            id: Stored category identity.

        Returns:
            The category, including inactive categories.

        Raises:
            NotFoundException: The identity is absent.
        """
        category = await self.repo.get_by_id(id)
        category = self._check_for_id_existence(id, category)
        return category

    async def list(self, query: CategoryList) -> PagedType[CategoryModel]:
        """Read the panel page with its selected filters.

        Args:
            query: Validated search and paging inputs.

        Returns:
            Categories ordered by priority and ID, with their total.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            is_active=query.is_active,
        )
        return page

    @transactional
    async def update(self, id: int, data: CategoryUpdate) -> CategoryModel:
        """Apply a patch while preserving the slug.

        Args:
            id: Stored category identity.
            data: Validated changes; description may be explicitly cleared.

        Returns:
            The updated category.

        Raises:
            NotFoundException: The identity is absent.
            ValidationException: The patch is empty.
        """
        changes = self._check_not_empty_dict(data.to_row())
        category = await self.repo.update_by_id(id, changes)
        category = self._check_for_id_existence(id, category)
        return category
