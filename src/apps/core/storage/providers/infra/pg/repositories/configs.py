"""Configuration persistence keyed by the owning storage connection."""

from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import (
    PGTimestampRepository,
)
from pydantic import JsonValue
from sqlalchemy import update
from sqlmodel import col

from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderConfigModel,
)
from src.apps.core.storage.providers.domain.results.records import (
    StorageProviderConfigSnapshot,
)
from src.apps.core.storage.providers.infra.pg.mappers.records import (
    StorageProviderMapper,
)
from src.apps.core.storage.providers.infra.pg.sql.records import (
    StorageProviderReadSQL,
)
from src.apps.core.storage.providers.infra.pg.tables import (
    StorageProviderConfigTable,
)


class StorageProviderConfigRepository(
    PGTimestampRepository[StorageProviderConfigModel]
):
    table = StorageProviderConfigTable

    async def get_by_provider_id(
        self, provider_id: int
    ) -> StorageProviderConfigModel | None:
        """Read one connection's configuration by its primary key.

        Args:
            provider_id: Exact owning storage connection ID.

        Returns:
            Stored configuration including an empty JSON object, or None
            when no configuration row exists.
        """
        configuration = await self.get_one(
            col(self.table.provider_id) == provider_id
        )
        return configuration

    async def get_by_provider_ids(
        self, provider_ids: Sequence[int]
    ) -> Sequence[StorageProviderConfigModel]:
        """Read a bounded set of configurations in one native IN selection.

        Args:
            provider_ids: Connection IDs bounded by the app caller.

        Returns:
            Found configurations once per connection, omitting missing IDs.
            Ordering is unspecified. Empty input performs no I/O.
        """
        configurations: Sequence[StorageProviderConfigModel] = []
        if provider_ids:
            configurations = await self.get_all(
                col(self.table.provider_id).in_(provider_ids)
            )
        return configurations

    async def update_by_provider_id(
        self,
        provider_id: int,
        config: dict[str, JsonValue],
    ) -> StorageProviderConfigModel | None:
        """Replace one connection's entire stored JSON configuration.

        Args:
            provider_id: Exact owning connection ID.
            config: Complete replacement JSON object; {} is valid. Values
                are neither merged nor interpreted as S3 settings here.

        Returns:
            The updated configuration, or None if no row exists. Transaction
            completion belongs to the caller.
        """
        stmt = (
            update(self.table)
            .where(col(self.table.provider_id) == provider_id)
            .values(config=config)
            .returning(self.table)
            .execution_options(
                populate_existing=True, synchronize_session=False
            )
        )
        result = await self.uow.execute(stmt)
        configuration = result.scalar_one_or_none()
        return configuration

    async def find_active(self) -> StorageProviderConfigSnapshot | None:
        """Read only the active connection ID and configuration in one query.

        Args:
            None.

        Returns:
            A materialized snapshot, or None when no connection is active.
            Missing configuration remains None and an empty object stays {}.
        """
        stmt = StorageProviderReadSQL.select_active_configuration()
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        snapshot = (
            None
            if row is None
            else StorageProviderMapper.to_config_snapshot(row)
        )
        return snapshot
