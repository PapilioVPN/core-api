"""Configuration record operations backed by one native repository."""

from collections.abc import Sequence

from papilio.core import resources
from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import Checks

from src.apps.core.storage.providers.app.helpers.records import (
    prepare_connection,
)
from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderBatchRead,
)
from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderConfigModel,
)
from src.apps.core.storage.providers.domain.results.records import (
    StorageProviderConnection,
)
from src.apps.core.storage.providers.infra.pg.repositories.configs import (
    StorageProviderConfigRepository,
)


class StorageProviderConfigService(Checks[StorageProviderConfigModel]):
    entity = "StorageProviderConfig"

    def __init__(self, repo: StorageProviderConfigRepository) -> None:
        """Bind configuration persistence on the current request's UoW.

        Args:
            repo: Native connection configuration repository.

        Returns:
            None.
        """
        self.repo = repo

    @handle_conflicts(entity="StorageProviderConfig")
    @transactional
    async def create(
        self, provider_id: int, data: S3Config | None = None
    ) -> StorageProviderConfigModel:
        """Store configuration for a parent verified by the owning command.

        Args:
            provider_id: Parent connection ID checked by the command.
            data: Complete typed settings; omitted input stores {}.

        Returns:
            Stored JSON with supplied credentials and all DTO defaults.

        Raises:
            ConflictException: A configuration already exists for this parent.
            IntegrityError: The referenced parent no longer exists.
        """
        configuration = await self.repo.create(
            StorageProviderConfigModel(
                provider_id=provider_id,
                config={}
                if data is None
                else data.to_row(exclude_unset=False),
            )
        )
        return configuration

    async def get_by_provider_id(
        self, provider_id: int
    ) -> StorageProviderConfigModel:
        """Read a stored configuration that must exist.

        Args:
            provider_id: Exact owning connection identity.

        Returns:
            Raw internal configuration, including an empty JSON object.

        Raises:
            NotFoundException: The configuration row is absent.
        """
        configuration = await self.repo.get_by_provider_id(provider_id)
        configuration = self._check_for_existence(
            "provider_id", provider_id, configuration
        )
        return configuration

    async def find_by_provider_id(
        self, provider_id: int
    ) -> StorageProviderConfigModel | None:
        """Read an optional stored configuration without making defaults.

        Args:
            provider_id: Exact owning connection identity.

        Returns:
            Stored configuration, including {}; None when absent.
        """
        configuration = await self.repo.get_by_provider_id(provider_id)
        return configuration

    async def get_by_provider_ids(
        self, data: StorageProviderBatchRead
    ) -> Sequence[StorageProviderConfigModel]:
        """Read configurations through one native bounded set selection.

        Args:
            data: One to 100 connection IDs, including possible duplicates.

        Returns:
            Found rows once each, omitting misses; ordering is unspecified.
        """
        configurations = await self.repo.get_by_provider_ids(data.ids)
        return configurations

    @transactional
    async def update(
        self, provider_id: int, data: S3Config
    ) -> StorageProviderConfigModel:
        """Replace the complete configuration for a command-verified parent.

        Args:
            provider_id: Exact connection ID checked by the owning command.
            data: Validated replacement settings, including DTO defaults.

        Returns:
            Updated stored configuration; previous keys are not merged.

        Raises:
            NotFoundException: The configuration row is absent.
        """
        configuration = await self.repo.update_by_provider_id(
            provider_id, data.to_row(exclude_unset=False)
        )
        configuration = self._check_for_existence(
            "provider_id", provider_id, configuration
        )
        return configuration

    async def get_connection(
        self, provider_id: int
    ) -> StorageProviderConnection:
        """Require the recorded connection's usable settings.

        Args:
            provider_id: Exact recorded ID, irrespective of current activity.

        Returns:
            Materialized identity and typed configuration for that connection.

        Raises:
            NotFoundException: The configuration row is absent.
            ValidationException: Stored settings are empty or invalid.
        """
        configuration = await self.get_by_provider_id(provider_id)
        connection = prepare_connection(provider_id, configuration.config)
        return connection

    async def get_active_connection(self) -> StorageProviderConnection:
        """Require only the active connection ID and usable configuration.

        Args:
            None.

        Returns:
            Materialized identity and typed settings without metadata or I/O
            beyond the single database read.

        Raises:
            NotFoundException: No connection is active.
            ValidationException: Stored settings are absent, empty or invalid.
        """
        snapshot = await self.repo.find_active()
        if snapshot is None:
            raise NotFoundException(
                message="Cannot find an active storage provider",
                message_code=resources.NOT_FOUND_ERROR,
                entity="StorageProvider",
                identifier="is_active",
                identifier_value=True,
            )
        connection = prepare_connection(snapshot.provider_id, snapshot.config)
        return connection
