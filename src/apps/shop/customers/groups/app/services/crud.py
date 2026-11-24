"""Manage customer group definitions with native record operations."""

from collections.abc import Sequence

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import GroupCreate, GroupList, GroupUpdate
from ...domain.models.records import CustomerGroupModel
from ...infra.pg.repositories.crud import CustomerGroupRepository


class CustomerGroupService(IDChecks[CustomerGroupModel]):
    entity = "CustomerGroup"

    def __init__(self, repo: CustomerGroupRepository) -> None:
        """Bind the request's group repository.

        Args:
            repo: Native PostgreSQL customer group repository.

        Returns:
            None.
        """
        self.repo = repo

    @handle_conflicts
    @transactional
    async def create(self, data: GroupCreate) -> CustomerGroupModel:
        """Register a group and its qualifying purchase total.

        Args:
            data: Validated group definition and minimum spend in rials.

        Returns:
            The stored group and its assigned identity.

        Raises:
            ConflictException: The key or minimum spend is already in use.
        """
        group = await self.repo.create(
            CustomerGroupModel(
                key=data.key,
                title=data.title,
                min_spend=data.min_spend,
                is_active=data.is_active,
                priority=data.priority,
            )
        )
        return group

    async def get_by_id(self, id: int) -> CustomerGroupModel:
        """Read a group by identity.

        Args:
            id: Stored group identity.

        Returns:
            The matching group, including inactive groups.

        Raises:
            NotFoundException: No group has this identity.
        """
        group = await self.repo.get_by_id(id)
        return self._check_for_id_existence(id, group)

    async def get_by_key(self, key: str) -> CustomerGroupModel:
        """Read a group by its exact key.

        Args:
            key: Stored group key.

        Returns:
            The matching group, including inactive groups.

        Raises:
            NotFoundException: No group has this key.
        """
        group = await self.repo.find_by_key(key)
        return self._check_for_existence("key", key, group)

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CustomerGroupModel]:
        """Read groups through one bounded native selection.

        Args:
            ids: Stored group identities.

        Returns:
            Unique group matches with missing identities omitted.
        """
        groups = await self.repo.get_by_ids(ids) if ids else []
        return groups

    async def list(self, query: GroupList) -> PagedType[CustomerGroupModel]:
        """Read a filtered group page.

        Args:
            query: Validated panel search, activity and paging inputs.

        Returns:
            A priority-ordered page with its filtered total.
        """
        groups = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            q=query.q,
            is_active=query.is_active,
        )
        return groups

    @handle_conflicts
    @transactional
    async def update(self, id: int, data: GroupUpdate) -> CustomerGroupModel:
        """Edit a group definition.

        Args:
            id: Stored group identity.
            data: Validated changes; omitted fields keep their values.

        Returns:
            The updated group.

        Raises:
            NotFoundException: The group is absent.
            ValidationException: The patch has no recognized fields.
            ConflictException: A group already uses the requested threshold.
        """
        changes = self._check_not_empty_dict(data.to_row())
        group = await self.repo.update_by_id(id, changes)
        return self._check_for_id_existence(id, group)

    @transactional
    async def remove(self, id: int) -> CustomerGroupModel:
        """Remove an unassigned group.

        Args:
            id: Stored group identity.

        Returns:
            The removed group.

        Raises:
            NotFoundException: The group is absent.
            ConflictException: At least one profile references the group.
        """
        group = await self.repo.remove_by_id(id)
        return self._check_for_id_existence(id, group)
