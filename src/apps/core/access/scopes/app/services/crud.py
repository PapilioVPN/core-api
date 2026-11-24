"""Scope orchestration with native transactions and conflict handling."""

from collections.abc import Sequence

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.core.access.scopes.domain.dtos.records import (
    ScopeCreate,
    ScopeList,
    ScopeUpdate,
)
from src.apps.core.access.scopes.domain.models.records import ScopeModel
from src.apps.core.access.scopes.infra.pg.repositories.crud import (
    ScopeRepository,
)


class ScopeService(IDChecks[ScopeModel]):
    entity = "Scope"

    def __init__(self, repo: ScopeRepository) -> None:
        """Bind this request's scope repository.

        Args:
            repo: Native PostgreSQL repository on the request's UoW.

        Returns:
            None.
        """
        self.repo = repo

    @handle_conflicts(entity="Scope")
    @transactional
    async def create(self, data: ScopeCreate) -> ScopeModel:
        """Create a scope with an exact user-defined key.

        Args:
            data: Validated scope fields, including the initial active flag.

        Returns:
            The stored scope with its database identity and timestamps.

        Raises:
            ConflictException: A scope already has this exact key.
        """
        scope = await self.repo.create(
            ScopeModel(
                key=data.key,
                title=data.title,
                description=data.description,
                is_active=data.is_active,
            )
        )
        return scope

    async def get_by_id(self, id: int) -> ScopeModel:
        """Read a scope that must exist.

        Args:
            id: Stored scope identity.

        Returns:
            The scope, including inactive records.

        Raises:
            NotFoundException: The identity is absent.
        """
        scope = await self.repo.get_by_id(id)
        scope = self._check_for_id_existence(id, scope)
        return scope

    async def find_by_id(self, id: int) -> ScopeModel | None:
        """Look up a scope without requiring its existence.

        Args:
            id: Stored scope identity.

        Returns:
            The scope, including inactive records; None when absent.
        """
        scope = await self.repo.get_by_id(id)
        return scope

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[ScopeModel]:
        """Read matching scopes with one native set selection.

        Args:
            ids: Bounded scope identities supplied by the app caller.

        Returns:
            Matching scopes, including inactive ones; missing IDs are omitted,
            repeated IDs appear once, and order is unspecified.
        """
        scopes = await self.repo.get_by_ids(ids)
        return scopes

    async def find_by_key(self, key: str) -> ScopeModel | None:
        """Look up a scope by its unchanged user-defined key.

        Args:
            key: Exact, case-sensitive scope key.

        Returns:
            The scope, including inactive records; None when absent.
        """
        scope = await self.repo.find_by_key(key)
        return scope

    async def list(self, query: ScopeList) -> PagedType[ScopeModel]:
        """List matching scopes using application-owned pagination.

        Args:
            query: Native page/per_page and optional title/state filters.

        Returns:
            An ID-ordered page and its filtered total before pagination.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            title=query.title,
            is_active=query.is_active,
        )
        return page

    @transactional
    async def update(self, id: int, data: ScopeUpdate) -> ScopeModel:
        """Apply supplied changes while preserving the scope key.

        Args:
            id: Stored scope identity.
            data: Validated patch; description may be cleared.

        Returns:
            The updated scope, preserving every omitted field.

        Raises:
            NotFoundException: The identity is absent.
            ValidationException: No update fields were supplied.
        """
        changes = self._check_not_empty_dict(data.to_row())
        scope = await self.repo.update_by_id(id, changes)
        scope = self._check_for_id_existence(id, scope)
        return scope

    @transactional
    async def remove(self, id: int) -> ScopeModel:
        """Delete one scope through the native transaction boundary.

        Args:
            id: Stored scope identity.

        Returns:
            The scope as it was immediately before deletion.

        Raises:
            NotFoundException: The identity is absent.
        """
        scope = await self.repo.remove_by_id(id)
        scope = self._check_for_id_existence(id, scope)
        return scope
