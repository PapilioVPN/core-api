"""Coordinated storage metadata, configuration and activation contracts."""

from typing import Protocol

from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderActivityUpdate,
    StorageProviderCreate,
)
from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderConfigModel,
    StorageProviderModel,
)


class IStorageProviderCreateCommand(Protocol):
    """Create inactive metadata and one configuration in the same transaction.

    Omitted configuration creates an empty JSON object. Native duplicate-key
    conflicts propagate. Both records commit or roll back together.
    """

    async def create(
        self, data: StorageProviderCreate, config: S3Config | None = None
    ) -> StorageProviderModel: ...


class IStorageProviderConfigCommand(Protocol):
    """Require the parent, then replace its complete configuration."""

    async def update(
        self, provider_id: int, data: S3Config
    ) -> StorageProviderConfigModel: ...


class IStorageProviderActivityCommand(Protocol):
    """Coordinate an atomic switch with at most one active connection.

    Disabling a connection changes only its flag. Enabling one disables the
    current connection first, within the same native transaction. The unique
    database index remains authoritative for concurrent activation conflicts.
    """

    async def update(
        self, id: int, data: StorageProviderActivityUpdate
    ) -> StorageProviderModel: ...
