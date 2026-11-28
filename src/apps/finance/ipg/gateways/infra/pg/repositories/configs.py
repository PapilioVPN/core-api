"""Read and replace encrypted configurations by provider key."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from pydantic import JsonValue
from sqlalchemy import update
from sqlmodel import col

from ....domain.enums.records import GatewayKind
from ....domain.models.configs import ConfigModel
from ..tables import IPGConfigTable


class ConfigRepository(PGPersistenceRepository[ConfigModel]):
    table = IPGConfigTable

    async def find(self, key: GatewayKind) -> ConfigModel | None:
        """Read the current configuration for the provider key, if saved."""
        config = await self.get_one(col(self.table.key) == key)
        return config

    async def replace(
        self, key: GatewayKind, data: dict[str, JsonValue]
    ) -> ConfigModel | None:
        """Replace the encrypted configuration for the given key."""
        table = self.table
        stmt = (
            update(table)
            .where(col(table.key) == key)
            .values(config=data)
            .returning(table)
            .execution_options(
                populate_existing=True, synchronize_session=False
            )
        )
        result = await self.uow.execute(stmt)
        config = result.scalar_one_or_none()
        return config
