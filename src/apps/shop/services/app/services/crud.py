"""Manage service definitions shared by the shop's operators."""

from collections.abc import Sequence

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.shop.services.domain.dtos.records import (
    ServiceCreate,
    ServiceList,
    ServiceUpdate,
)
from src.apps.shop.services.domain.models.records import ServiceModel
from src.apps.shop.services.infra.pg.repositories.crud import (
    ServiceRepository,
)


class ServiceCRUD(IDChecks[ServiceModel]):
    entity = "Service"

    def __init__(self, repo: ServiceRepository) -> None:
        """Bind the request's service repository."""
        self.repo = repo

    @transactional
    async def create(self, data: ServiceCreate) -> ServiceModel:
        """Register a service for sale.

        Args:
            data: Validated service profile, priority and initial sales state.

        Returns:
            The stored service with its identity and timestamps.
        """
        service = await self.repo.create(
            ServiceModel(
                title=data.title,
                description=data.description,
                is_active=data.is_active,
                priority=data.priority,
            )
        )
        return service

    async def get_by_id(self, id: int) -> ServiceModel:
        """Read a service by its stable identity.

        Args:
            id: Stored service identity.

        Returns:
            The service in its current sales state.

        Raises:
            NotFoundException: The identity is absent.
        """
        service = await self.find_by_id(id)
        service = self._check_for_id_existence(id, service)
        return service

    @transactional
    async def remove(self, id: int) -> ServiceModel:
        """Remove an unreferenced service and return its stored record."""
        service = await self.repo.remove_by_id(id)
        service = self._check_for_id_existence(id, service)
        return service

    async def find_by_id(self, id: int) -> ServiceModel | None:
        """Read a stored identity, returning None if it is absent."""
        service = await self.repo.get_by_id(id)
        return service

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[ServiceModel]:
        """Read a bounded set in one query, omitting absent identities."""
        rows = await self.repo.get_by_ids(ids) if ids else []
        return rows

    async def list(self, query: ServiceList) -> PagedType[ServiceModel]:
        """Read a filtered page for the administrator panel.

        Args:
            query: Validated search, state and paging inputs.

        Returns:
            A page ordered by increasing priority and ID, with its total.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            is_active=query.is_active,
        )
        return page

    @transactional
    async def update(self, id: int, data: ServiceUpdate) -> ServiceModel:
        """Update the supplied service fields.

        Args:
            id: Stored service identity.
            data: Validated changes, including an explicit sales state or
                cleared description where supplied.

        Returns:
            The updated service, preserving omitted fields.

        Raises:
            NotFoundException: The identity is absent.
            ValidationException: The patch has no recognized fields.
        """
        changes = self._check_not_empty_dict(data.to_row())
        service = await self.repo.update_by_id(id, changes)
        service = self._check_for_id_existence(id, service)
        return service
