"""Short metadata operations backed by one native PostgreSQL repository."""

from collections.abc import Sequence

from papilio.core import resources
from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderBatchRead,
    StorageProviderCreate,
    StorageProviderKeyBatchRead,
    StorageProviderList,
    StorageProviderUpdate,
)
from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderModel,
)
from src.apps.core.storage.providers.infra.pg.repositories.records import (
    StorageProviderRepository,
)


class StorageProviderService(IDChecks[StorageProviderModel]):
    entity = "StorageProvider"

    def __init__(self, repo: StorageProviderRepository) -> None:
        """Bind metadata persistence on the current request's UoW.

        Args:
            repo: Native storage connection repository.

        Returns:
            None.
        """
        self.repo = repo

    @handle_conflicts(entity="StorageProvider")
    @transactional
    async def create(
        self, data: StorageProviderCreate
    ) -> StorageProviderModel:
        """Create inactive connection metadata without configuration.

        Args:
            data: Validated user-defined key and descriptive fields.

        Returns:
            Inactive metadata with its stored identity and timestamps.

        Raises:
            ConflictException: Another connection already uses this key.
        """
        provider = await self.repo.create(
            StorageProviderModel(
                key=data.key,
                title=data.title,
                description=data.description,
            )
        )
        return provider

    async def get_by_id(self, id: int) -> StorageProviderModel:
        """Read connection metadata that must exist.

        Args:
            id: Exact internal connection identity, including inactive ones.

        Returns:
            Stored metadata without credentials or configuration.

        Raises:
            NotFoundException: No connection has this identity.
        """
        provider = await self.repo.get_by_id(id)
        provider = self._check_for_id_existence(id, provider)
        return provider

    async def find_by_id(self, id: int) -> StorageProviderModel | None:
        """Read optional connection metadata.

        Args:
            id: Exact internal connection identity.

        Returns:
            Stored metadata, or None when absent.
        """
        provider = await self.repo.get_by_id(id)
        return provider

    async def find_by_key(self, key: str) -> StorageProviderModel | None:
        """Read optional metadata by an exact key.

        Args:
            key: Case-sensitive stored key, passed unchanged.

        Returns:
            Stored metadata, or None when absent.
        """
        provider = await self.repo.find_by_key(key)
        return provider

    async def get_by_ids(
        self, data: StorageProviderBatchRead
    ) -> Sequence[StorageProviderModel]:
        """Read a bounded set through one native selection.

        Args:
            data: One to 100 connection IDs, including possible duplicates.

        Returns:
            Found metadata once each, omitting misses; order is unspecified.
        """
        providers = await self.repo.get_by_ids(data.ids)
        return providers

    async def get_by_keys(
        self, data: StorageProviderKeyBatchRead
    ) -> Sequence[StorageProviderModel]:
        """Read a bounded set of exact keys through one selection.

        Args:
            data: One to 100 validated connection keys.

        Returns:
            Found metadata in ascending ID order, omitting misses and repeats.
        """
        providers = await self.repo.get_by_keys(data.keys)
        return providers

    async def find_active(self) -> StorageProviderModel | None:
        """Read the active connection's metadata without configuration.

        Args:
            None.

        Returns:
            Active metadata, or None when none is active.
        """
        provider = await self.repo.find_active()
        return provider

    async def find_active_id(self) -> int | None:
        """Read only the optional active connection identity.

        Args:
            None.

        Returns:
            The active connection ID, or None when none is active.
        """
        provider_id = await self.repo.find_active_id()
        return provider_id

    async def get_active_id(self) -> int:
        """Require the active connection identity without loading metadata.

        Args:
            None.

        Returns:
            The stored active connection ID.

        Raises:
            NotFoundException: No connection is active.
        """
        provider_id = await self.repo.find_active_id()
        if provider_id is None:
            raise NotFoundException(
                message="Cannot find an active storage provider",
                message_code=resources.NOT_FOUND_ERROR,
                entity=self.entity,
                identifier="is_active",
                identifier_value=True,
            )
        return provider_id

    async def list(
        self, query: StorageProviderList
    ) -> PagedType[StorageProviderModel]:
        """List metadata with application-owned page conversion.

        Args:
            query: Native paging and optional literal title/activity filters.

        Returns:
            An ID-ordered page and the matching total before pagination.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            title=query.title,
            is_active=query.is_active,
        )
        return page

    @transactional
    async def update(
        self, id: int, data: StorageProviderUpdate
    ) -> StorageProviderModel:
        """Patch descriptive fields while preserving key and activity.

        Args:
            id: Existing internal connection identity.
            data: Explicit title/description changes; null clears description.

        Returns:
            Updated metadata, preserving every omitted field.

        Raises:
            ValidationException: The recognized patch is empty.
            NotFoundException: The connection is absent.
        """
        changes = self._check_not_empty_dict(data.to_row())
        provider = await self.repo.update_by_id(id, changes)
        provider = self._check_for_id_existence(id, provider)
        return provider

    @handle_conflicts(entity="StorageProvider")
    @transactional
    async def set_active(
        self, id: int, is_active: bool
    ) -> StorageProviderModel:
        """Set one connection's flag without switching other connections.

        Args:
            id: Existing internal connection identity.
            is_active: Target flag; False disables this connection.

        Returns:
            Updated metadata for this connection only.

        Raises:
            NotFoundException: The connection is absent.
            ConflictException: Another connection is already active.
        """
        provider = await self.repo.update_by_id(id, {"is_active": is_active})
        provider = self._check_for_id_existence(id, provider)
        return provider

    @transactional
    async def remove(self, id: int) -> StorageProviderModel:
        """Remove one connection; the database cascades its configuration.

        Args:
            id: Exact internal connection identity.

        Returns:
            Metadata as it was before removal.

        Raises:
            NotFoundException: The connection is absent.
        """
        provider = await self.repo.remove_by_id(id)
        provider = self._check_for_id_existence(id, provider)
        return provider
