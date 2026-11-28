"""Register each authenticated delivery at most once per account."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.models.deliveries import DeliveryModel
from ..tables import CardGatewayDeliveryTable


class DeliveryRepository(PGIdentifiedRepository[DeliveryModel]):
    table = CardGatewayDeliveryTable

    async def record(self, data: DeliveryModel) -> int | None:
        """Register a new delivery in the caller's confirmation transaction.

        Args:
            data: Verified provider notification and its intake timestamp.

        Returns:
            The inserted row ID, or None when the delivery already exists.
        """
        table = self.table
        stmt = (
            insert(table)
            .values(data.to_row())
            .on_conflict_do_nothing(
                index_elements=[col(table.gateway_id), col(table.delivery_id)]
            )
            .returning(col(table.id))
        )
        result = await self.uow.execute(stmt)
        id = result.scalar_one_or_none()
        return id
