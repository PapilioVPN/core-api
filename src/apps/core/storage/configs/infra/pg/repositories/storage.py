"""Global storage destination reads and atomic native upsert."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from sqlalchemy import func, literal_column, select
from sqlmodel import col

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.configs.domain.models.storage import (
    StorageConfigModel,
)
from src.apps.core.storage.configs.infra.pg.tables import StorageConfigTable


class StorageConfigRepository(PGPersistenceRepository[StorageConfigModel]):
    table = StorageConfigTable

    async def get_current(self) -> StorageConfigModel | None:
        """Read the one global configuration from the current SQL snapshot.

        Args:
            None.

        Returns:
            Materialized settings, or None when no setting is stored. Already
            loaded records are refreshed; no backend or provider is invented.
        """
        stmt = select(self.table).execution_options(populate_existing=True)
        result = await self.uow.execute(stmt)
        configuration = result.scalar_one_or_none()
        return configuration

    async def get_backend(self) -> StorageBackend | None:
        """Read only the stored destination kind, without record metadata.

        Args:
            None.

        Returns:
            The selected backend, or None if the global setting is absent.
        """
        stmt = select(col(self.table.backend))
        result = await self.uow.execute(stmt)
        backend = result.scalar_one_or_none()
        return backend

    async def save(self, backend: StorageBackend) -> StorageConfigModel:
        """Create or replace the global selection in one native upsert.

        Args:
            backend: Trusted explicit storage mechanism selected by the caller.

        Returns:
            Stored settings with stable identity/creation time on replacement.
            The singleton expression index coordinates concurrent first saves;
            updated_at records this write. The caller owns commit/rollback.
        """
        columns = StorageConfigTable.__table__.c
        configuration = await self.upsert(
            StorageConfigModel(backend=backend),
            conflict_columns=[literal_column("(true)")],
            update_columns=[columns.backend],
            changes={columns.updated_at: func.current_timestamp()},
        )
        return configuration
