"""Maintain attribute definitions and their typed parameter bindings."""

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.catalog.attributes.domain.dtos.records import (
    AttributeCreate,
    AttributeList,
    AttributeUpdate,
)
from src.apps.catalog.attributes.domain.dtos.validators.params import (
    check_param,
)
from src.apps.catalog.attributes.domain.models.records import AttributeModel
from src.apps.catalog.attributes.infra.pg.repositories.records import (
    AttributeRepository,
)


class AttributeService(IDChecks[AttributeModel]):
    entity = "Attribute"

    def __init__(self, repo: AttributeRepository) -> None:
        """Bind the request's attribute repository."""
        self.repo = repo

    @handle_conflicts
    @transactional
    async def create(self, data: AttributeCreate) -> AttributeModel:
        """Register a reusable feature definition.

        Args:
            data: Validated attribute fields.

        Returns:
            The stored attribute.

        Raises:
            ConflictException: The key or parameter is already registered.
        """
        attribute = await self.repo.create(
            AttributeModel(
                key=data.key,
                label=data.label,
                type=data.type,
                description=data.description,
                param_key=data.param_key,
                is_active=data.is_active,
            )
        )
        return attribute

    async def get_by_id(self, id: int) -> AttributeModel:
        """Read one attribute.

        Args:
            id: Stored attribute identity.

        Returns:
            The attribute, including inactive definitions.

        Raises:
            NotFoundException: The identity is absent.
        """
        attribute = await self.repo.get_by_id(id)
        attribute = self._check_for_id_existence(id, attribute)
        return attribute

    async def list(self, query: AttributeList) -> PagedType[AttributeModel]:
        """Read a filtered page of feature definitions.

        Args:
            query: Validated search and paging inputs.

        Returns:
            Matching attributes and their total before pagination.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            is_active=query.is_active,
        )
        return page

    @handle_conflicts
    @transactional
    async def update(self, id: int, data: AttributeUpdate) -> AttributeModel:
        """Change labels, visibility or the parameter binding.

        Args:
            id: Stored attribute identity.
            data: Validated changes, with explicit null clearing the binding.

        Returns:
            The updated attribute with its original key and type.

        Raises:
            NotFoundException: The identity is absent.
            ValidationException: The patch is empty or incompatible.
            ConflictException: Another attribute owns the parameter.
        """
        changes = self._check_not_empty_dict(data.to_row())
        if data.param_key is not None:
            attribute = await self.get_by_id(id)
            check_param(attribute.type, data.param_key)
        attribute = await self.repo.update_by_id(id, changes)
        attribute = self._check_for_id_existence(id, attribute)
        return attribute
