"""Metadata and configuration record services, each owning one repository."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderBatchRead,
    StorageProviderCreate,
    StorageProviderKeyBatchRead,
    StorageProviderList,
    StorageProviderUpdate,
)
from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderConfigModel,
    StorageProviderModel,
)
from src.apps.core.storage.providers.domain.results.records import (
    StorageProviderConnection,
)


class IStorageProviderService(Protocol):
    """Connection metadata without credentials or manual transaction control.

    Creation starts inactive. Key stays fixed after creation. Optional find
    operations return None; required get/update/remove operations raise native
    NotFoundException on absence. Empty recognized patches raise native
    ValidationException. ID batches omit missing records and repeats with no
    ordering guarantee; key batches use ascending ID order. Listing returns an
    ID-ordered page with the filtered total and translates page/per_page here.
    Native transactional decorators commit independent writes or join the
    caller's current transaction; a record service performs no manual commit.
    """

    async def create(
        self, data: StorageProviderCreate
    ) -> StorageProviderModel: ...
    async def get_by_id(self, id: int) -> StorageProviderModel: ...
    async def find_by_id(self, id: int) -> StorageProviderModel | None: ...
    async def find_by_key(self, key: str) -> StorageProviderModel | None: ...
    async def get_by_ids(
        self, data: StorageProviderBatchRead
    ) -> Sequence[StorageProviderModel]: ...
    async def get_by_keys(
        self, data: StorageProviderKeyBatchRead
    ) -> Sequence[StorageProviderModel]: ...
    async def find_active(self) -> StorageProviderModel | None: ...
    async def find_active_id(self) -> int | None: ...
    async def get_active_id(self) -> int: ...
    async def list(
        self, query: StorageProviderList
    ) -> PagedType[StorageProviderModel]: ...
    async def update(
        self, id: int, data: StorageProviderUpdate
    ) -> StorageProviderModel: ...
    async def set_active(
        self, id: int, is_active: bool
    ) -> StorageProviderModel:
        """Set one activity flag; the activity command coordinates switching.

        Args:
            id: Existing connection identity.
            data: Activity flag to persist on this connection.

        Returns:
            Updated metadata, without changing other connections or committing.
        """
        ...

    async def remove(self, id: int) -> StorageProviderModel: ...


class IStorageProviderConfigService(Protocol):
    """Separate configuration storage and usable typed connection reads.

    Creation with omitted config stores {}. Writes replace the whole payload;
    configuration follows its provider's lifetime with no independent delete.
    Required get/update operations raise native NotFoundException on absence;
    find returns None. Batch reads omit missing IDs and repeats; order is
    unspecified. These operations do not activate connections. Native
    transactional decorators commit independent writes or join the caller's
    current transaction; a record service performs no manual commit.
    Parent existence is checked through IStorageProviderService by the command.
    Stored models contain internal credentials and are not HTTP output schemas.
    """

    async def create(
        self, provider_id: int, data: S3Config | None = None
    ) -> StorageProviderConfigModel: ...
    async def get_by_provider_id(
        self, provider_id: int
    ) -> StorageProviderConfigModel: ...
    async def find_by_provider_id(
        self, provider_id: int
    ) -> StorageProviderConfigModel | None: ...
    async def get_by_provider_ids(
        self, data: StorageProviderBatchRead
    ) -> Sequence[StorageProviderConfigModel]: ...
    async def update(
        self, provider_id: int, data: S3Config
    ) -> StorageProviderConfigModel: ...

    async def get_connection(
        self, provider_id: int
    ) -> StorageProviderConnection:
        """Require one recorded connection's usable configuration.

        Args:
            provider_id: Exact stored connection ID, including inactive ones.

        Returns:
            Materialized connection ID and validated S3 configuration.

        Raises:
            NotFoundException: The configuration row is absent.
            ValidationException: Stored JSON is empty or invalid.
        """
        ...

    async def get_active_connection(self) -> StorageProviderConnection:
        """Require only the active connection ID and usable configuration.

        Args:
            None.

        Returns:
            Materialized connection ID and validated S3 configuration without
            descriptive metadata or a remote connection probe.

        Raises:
            NotFoundException: No connection is active.
            ValidationException: Its configuration is absent, empty or invalid.
        """
        ...
