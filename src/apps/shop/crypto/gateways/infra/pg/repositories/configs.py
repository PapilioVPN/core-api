"""Persist one encrypted JSON configuration per crypto gateway."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGTimestampRepository,
)
from sqlalchemy import func
from sqlmodel import col

from ....domain.models.records import CryptoGatewayConfigModel
from ..tables import CryptoGatewayConfigTable


class CryptoGatewayConfigRepository(
    PGTimestampRepository[CryptoGatewayConfigModel]
):
    table = CryptoGatewayConfigTable

    async def find_by_gateway_id(
        self, id: int
    ) -> CryptoGatewayConfigModel | None:
        """Read the configuration for one authoritative gateway ID."""
        record = await self.get_one(col(self.table.gateway_id) == id)
        return record

    async def save(
        self, data: CryptoGatewayConfigModel
    ) -> CryptoGatewayConfigModel:
        """Replace the settings by gateway ID and return the stored row.

        Args:
            data: Complete encrypted configuration and its owner ID.

        Returns:
            The row inserted or updated by native PostgreSQL upsert.
        """
        columns = CryptoGatewayConfigTable.__table__.c
        record = await self.upsert(
            data,
            conflict_columns=[columns.gateway_id],
            update_columns=[columns.config],
            changes={columns.updated_at: func.current_timestamp()},
        )
        return record
