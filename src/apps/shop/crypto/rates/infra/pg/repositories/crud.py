"""Persist one observed rate per pricing currency."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)

from ....domain.models.records import CryptoRateModel
from ..tables import CryptoRateTable


class CryptoRateRepository(PGIdentifiedRepository[CryptoRateModel]):
    table = CryptoRateTable

    async def save(self, data: CryptoRateModel) -> CryptoRateModel:
        """Store the prepared rate, retaining the identity of its currency."""
        fields = CryptoRateTable.__table__.c
        rate = await self.upsert(
            data,
            conflict_columns=[fields.currency],
            update_columns=[
                fields.rial_rate,
                fields.source,
                fields.fetched_at,
            ],
        )
        return rate
