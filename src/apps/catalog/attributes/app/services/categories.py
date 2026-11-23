"""Assign and read reusable attributes under their categories."""

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import Checks

from src.apps.catalog.attributes.app.services.records import AttributeService
from src.apps.catalog.attributes.domain.dtos.categories import (
    BindingList,
    BindingSave,
)
from src.apps.catalog.attributes.domain.models.categories import (
    CategoryAttributeModel,
)
from src.apps.catalog.attributes.domain.results.categories import BindingDetail
from src.apps.catalog.attributes.infra.pg.repositories.categories import (
    BindingRepository,
)
from src.apps.catalog.categories.app.interfaces.services import (
    ICategoryService,
)


class BindingService(Checks[CategoryAttributeModel]):
    entity = "Category attribute"

    def __init__(
        self,
        repo: BindingRepository,
        categories: ICategoryService,
        attributes: AttributeService,
    ) -> None:
        """Bind persistence and identity checks to one request."""
        self.repo = repo
        self.categories = categories
        self.attributes = attributes

    @transactional
    async def save(
        self, category_id: int, attribute_id: int, data: BindingSave
    ) -> CategoryAttributeModel:
        """Set the category-specific settings for one feature.

        Args:
            category_id: Category receiving the feature.
            attribute_id: Existing feature definition.
            data: Validated assignment settings.

        Returns:
            The stored category-attribute binding.

        Raises:
            NotFoundException: The category or attribute is absent.
        """
        await self.categories.get_by_id(category_id)
        await self.attributes.get_by_id(attribute_id)
        binding = await self.repo.save(
            CategoryAttributeModel(
                category_id=category_id,
                attribute_id=attribute_id,
                is_required=data.is_required,
                is_filterable=data.is_filterable,
                is_variant_axis=data.is_variant_axis,
                priority=data.priority,
            )
        )
        return binding

    async def list(
        self, category_id: int, query: BindingList
    ) -> PagedType[BindingDetail]:
        """Read assigned features for the selected category.

        Args:
            category_id: Owning category identity.
            query: Validated page limits.

        Returns:
            Matching feature definitions with assignment settings.

        Raises:
            NotFoundException: The category is absent.
        """
        await self.categories.get_by_id(category_id)
        page = await self.repo.list(
            category_id,
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
        )
        return page

    @transactional
    async def remove(
        self, category_id: int, attribute_id: int
    ) -> CategoryAttributeModel:
        """Remove an assignment while retaining the feature definition.

        Args:
            category_id: Owning category identity.
            attribute_id: Feature identity.

        Returns:
            The removed binding.

        Raises:
            NotFoundException: The pair is absent.
        """
        binding = await self.repo.remove_from(category_id, attribute_id)
        binding = self._check_for_existence(
            "attribute_id", attribute_id, binding
        )
        return binding
