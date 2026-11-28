"""Confirm a card payment using a recorded bank transfer."""

from papilio.infra.db.tools.decorators import transactional
from papilio_tasks.apps.outbox import OutboxWriter

from ....settings.app.interfaces.services import ITransferSettingsService
from ....settings.domain.enums.records import SettingsKey
from ....transfers.app.interfaces.services import ITransferService
from ....transfers.domain.enums.records import TransferSource
from ...domain.events.records import PaymentConfirmed
from ...domain.models.records import CardPaymentModel
from ...infra.broker.publishers import payment_confirmed
from ..interfaces.services import ICardPaymentService


class ConfirmTransferCommand:
    def __init__(
        self,
        settings: ITransferSettingsService,
        transfers: ITransferService,
        payments: ICardPaymentService,
        outbox: OutboxWriter,
    ) -> None:
        self.settings = settings
        self.transfers = transfers
        self.payments = payments
        self.outbox = outbox

    @transactional
    async def confirm(self, transfer_id: int) -> CardPaymentModel | None:
        """Confirm an eligible transfer using the recorded bank timestamp.

        Args:
            transfer_id: Stored incoming transfer identity.

        Returns:
            The newly confirmed payment, or None when no change is needed.

        Raises:
            NotFoundException: The transfer is absent when confirmation is on.
        """
        payment = None
        settings = await self.settings.find(SettingsKey.GENERAL)
        if settings is not None and settings.auto_confirm:
            transfer = await self.transfers.get_by_id(transfer_id)
            if (
                transfer.source is TransferSource.HOOK
                and transfer.card_id is not None
                and transfer.transferred_at is not None
            ):
                payment = await self.payments.confirm_auto(
                    transfer_id=transfer.id,
                    card_id=transfer.card_id,
                    amount=transfer.amount,
                    transferred_at=transfer.transferred_at,
                )
                if payment is not None:
                    await self.outbox.append(
                        payment_confirmed,
                        PaymentConfirmed(payment_id=payment.id),
                    )
        return payment
