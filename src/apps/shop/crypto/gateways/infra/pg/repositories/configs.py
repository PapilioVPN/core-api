"""Persist each gateway's encrypted connection settings."""

from papilio.infra.db.repositories.backends.postgresql import PGRepository
from sqlmodel import col

from ....domain.models.configs import GatewayConfigModel
from ..tables import CryptoGatewayConfigTable


class GatewayConfigRepository(PGRepository[GatewayConfigModel]):
    table = CryptoGatewayConfigTable

    async def get(self, id: int) -> GatewayConfigModel | None:
        """Read settings for one stored gateway ID, or None if absent."""
        record = await self.get_one(col(self.table.gateway_id) == id)
        return record

    async def save(self, data: GatewayConfigModel) -> GatewayConfigModel:
        """Replace one gateway's configuration in a single write.

        Args:
            data: Owning account ID and its complete encrypted JSON settings.

        Returns:
            The stored settings.
        """
        fields = CryptoGatewayConfigTable.__table__.c
        record = await self.upsert(
            data,
            conflict_columns=[fields.gateway_id],
            update_columns=[fields.config],
        )
        return record
