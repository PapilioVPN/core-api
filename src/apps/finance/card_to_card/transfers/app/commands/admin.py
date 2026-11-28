"""Record an operator's transfer for an existing destination card."""

from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.shop.banking.payment_cards.app.interfaces.services import (
    IPaymentCardService,
)

from ...domain.dtos.records import AdminTransferCreate
from ...domain.enums.records import TransferSource
from ...domain.events.records import TransferCreated
from ...domain.models.records import TransferModel
from ...infra.broker.publishers import transfer_created
from ..interfaces.services import ITransferService


class AdminTransferCommand:
    def __init__(
        self,
        cards: IPaymentCardService,
        transfers: ITransferService,
        outbox: OutboxWriter,
    ) -> None:
        self.cards = cards
        self.transfers = transfers
        self.outbox = outbox

    @transactional
    async def create(
        self, data: AdminTransferCreate, *, admin_id: int
    ) -> TransferModel:
        """Resolve the selected card and store the operator entry.

        Args:
            data: Amount, destination card ID and optional bank timestamp.
            admin_id: Authenticated administrator identity.

        Returns:
            The stored transfer with a publication recorded for relay.

        Raises:
            NotFoundException: The selected card does not exist.
        """
        card = await self.cards.get_by_id(data.card_id)
        transfer = await self.transfers.create(
            TransferModel(
                amount=data.amount,
                card_id=card.id,
                transferred_at=data.transferred_at,
                created_at=utc_now(),
                source=TransferSource.ADMIN,
                source_id=admin_id,
            )
        )
        await self.outbox.append(
            transfer_created, TransferCreated(transfer_id=transfer.id)
        )
        return transfer
