"""Store the original business facts of an authenticated delivery."""

from papilio.utils.dates import utc_now

from ...domain.dtos.paid import PaidDelivery
from ...domain.models.deliveries import DeliveryModel
from ...infra.pg.repositories.deliveries import DeliveryRepository


class DeliveryService:
    def __init__(self, repo: DeliveryRepository) -> None:
        self.repo = repo

    async def record(self, delivery: PaidDelivery) -> int | None:
        """Persist normalized evidence in the caller's transaction.

        Args:
            delivery: Authenticated notification with rial amounts.

        Returns:
            The new delivery's database identity, or None for a replay.
        """
        transfer = delivery.transfer
        id = await self.repo.record(
            DeliveryModel(
                gateway_id=delivery.gateway_id,
                delivery_id=delivery.delivery_id,
                slug=transfer.slug,
                attempt_code=transfer.attempt_code,
                base_amount=transfer.base_amount,
                paid_amount=transfer.paid_amount,
                sent_at=transfer.sent_at,
                received_at=utc_now(),
            )
        )
        return id
