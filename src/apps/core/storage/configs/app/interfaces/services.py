"""Shared storage selection reads and record writes."""

from typing import Protocol

from src.apps.core.storage.configs.domain.dtos.storage import (
    StorageConfigWrite,
)
from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.configs.domain.models.storage import (
    StorageConfigModel,
)


class IStorageConfigService(Protocol):
    """Own one global record without selecting a provider or implicit default.

    Optional find operations return None on absence; required get operations
    raise native NotFoundException. Scalar reads select only backend. Save
    atomically creates or replaces the selection, retaining its identity and
    creation time. Native transaction ownership commits independent saves or
    joins the caller's transaction, whose final result remains provisional.
    Provider readiness and file transfer belong to their owning collaborators.
    """

    async def find_current(self) -> StorageConfigModel | None: ...
    async def get_current(self) -> StorageConfigModel: ...
    async def find_backend(self) -> StorageBackend | None: ...
    async def get_backend(self) -> StorageBackend: ...
    async def save(self, data: StorageConfigWrite) -> StorageConfigModel: ...
