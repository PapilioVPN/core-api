"""Record a bank hook notification and resolve its optional destination."""

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.shop.banking.payment_cards.app.interfaces.services import (
    IPaymentCardService,
)

from ...domain.dtos.records import HookTransferCreate
from ...domain.enums.records import TransferSource
from ...domain.events.records import TransferCreated
from ...domain.models.records import TransferModel
from ...infra.broker.publishers import transfer_created
from ..interfaces.services import ITransferService


class HookTransferCommand:
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
        self, data: HookTransferCreate, *, key_id: int
    ) -> TransferModel:
        """Resolve a supplied destination number and store the hook entry.

        Args:
            data: Amount, optional card number and optional bank timestamp.
            key_id: Authenticated API key identity.

        Returns:
            The stored transfer with a publication recorded for relay.
            Card ID is absent when no number is supplied.

        Raises:
            ValidationException: The supplied card number is not registered.
        """
        card_id = None
        if data.card_number is not None:
            card = await self.cards.find_by_number(data.card_number)
            if card is None:
                raise ValidationException(
                    message="The destination card is not registered.",
                    message_code="transfer_card_unknown",
                    loc=["card_number"],
                )
            card_id = card.id
        transfer = await self.transfers.create(
            TransferModel(
                amount=data.amount,
                card_id=card_id,
                transferred_at=data.transferred_at,
                created_at=utc_now(),
                source=TransferSource.HOOK,
                source_id=key_id,
            )
        )
        await self.outbox.append(
            transfer_created, TransferCreated(transfer_id=transfer.id)
        )
        return transfer
