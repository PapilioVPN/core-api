"""One-repository storage settings reads and native transactional saves."""

from papilio.core import resources
from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import Checks

from src.apps.core.storage.configs.domain.dtos.storage import (
    StorageConfigWrite,
)
from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.configs.domain.models.storage import (
    StorageConfigModel,
)
from src.apps.core.storage.configs.infra.pg.repositories.storage import (
    StorageConfigRepository,
)


class StorageConfigService(Checks[StorageConfigModel]):
    entity = "StorageConfig"

    def __init__(self, repo: StorageConfigRepository) -> None:
        """Bind the global settings repository on the current native UoW.

        Args:
            repo: Owning PostgreSQL settings repository.

        Returns:
            None.
        """
        self.repo = repo

    async def find_current(self) -> StorageConfigModel | None:
        """Read the optional global settings record.

        Args:
            None.

        Returns:
            Stored settings, or None when no selection has been saved.
        """
        configuration = await self.repo.get_current()
        return configuration

    async def get_current(self) -> StorageConfigModel:
        """Read the global settings record that must exist.

        Args:
            None.

        Returns:
            Stored settings without provider lookup or fabricated defaults.

        Raises:
            NotFoundException: The global setting is absent.
        """
        configuration = await self.repo.get_current()
        configuration = self._check_for_existence(
            "scope", "global", configuration
        )
        return configuration

    async def find_backend(self) -> StorageBackend | None:
        """Read the optional backend without fetching record metadata.

        Args:
            None.

        Returns:
            The stored backend; None when settings are absent.
        """
        backend = await self.repo.get_backend()
        return backend

    async def get_backend(self) -> StorageBackend:
        """Require the backend through the focused scalar selection.

        Args:
            None.

        Returns:
            The stored local/S3 selection without provider resolution.

        Raises:
            NotFoundException: The global setting is absent.
        """
        backend = await self.repo.get_backend()
        if backend is None:
            raise NotFoundException(
                message="Storage configuration is not configured",
                message_code=resources.NOT_FOUND_ERROR,
                entity=self.entity,
                identifier="scope",
                identifier_value="global",
            )
        return backend

    @transactional
    async def save(self, data: StorageConfigWrite) -> StorageConfigModel:
        """Create or replace the explicit global selection atomically.

        Args:
            data: Complete validated input containing the chosen backend.

        Returns:
            Stored settings with stable identity/creation time. Standalone
            saves commit; an existing caller transaction retains ownership.
        """
        configuration = await self.repo.save(data.backend)
        return configuration
