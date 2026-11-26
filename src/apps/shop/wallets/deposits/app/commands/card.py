"""Issue a wallet invoice for the selected card-to-card method."""

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional

from src.apps.shop.banking.banks.app.interfaces.queries import IBankQuery
from src.apps.shop.banking.payment_cards.app.interfaces.queries import (
    ICardPickQuery,
)
from src.apps.shop.banking.payment_cards.domain.enums.records import (
    PaymentMode,
)
from src.apps.shop.billing.payment_settings.app.interfaces.services import (
    IPaymentSettingsService,
)
from src.apps.shop.billing.payments.app.interfaces.commands import (
    IPaymentCommand,
)
from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)

from ...domain.dtos.records import CardDeposit
from ...domain.errors import DepositInvoiceUnavailable
from ...domain.models.records import CardPayment, DepositInvoice
from ..interfaces.services import IWalletDepositService


class CardInvoiceCommand:
    def __init__(
        self,
        customers: ICustomerService,
        deposits: IWalletDepositService,
        settings: IPaymentSettingsService,
        cards: ICardPickQuery,
        banks: IBankQuery,
        payments: IPaymentCommand,
    ) -> None:
        """Bind customer, card, Billing and invoice operations."""
        self.customers = customers
        self.deposits = deposits
        self.settings = settings
        self.cards = cards
        self.banks = banks
        self.payments = payments

    @transactional
    async def issue(
        self, customer_id: int, data: CardDeposit
    ) -> DepositInvoice:
        """Issue the card invoice and retain any automatic reservation.

        Args:
            customer_id: Identity of the customer requesting the top-up.
            data: Validated original amount in whole rials and chosen method.

        Returns:
            The cached invoice with transfer instructions and deadline.

        Raises:
            NotFoundException: The customer does not exist.
            ValidationException: The selected method has no eligible card.
            ConflictException: Billing cannot reserve a unique transfer amount.
            DepositInvoiceUnavailable: The invoice could not be stored.
        """
        await self.customers.get_by_id(customer_id)
        settings = await self.settings.get()
        mode = (
            PaymentMode.AUTO if settings.auto_confirm else PaymentMode.MANUAL
        )
        card = await self.cards.pick(mode)
        if card is None:
            raise ValidationException(
                message="No receiving card is available for this method.",
                message_code="deposit_method_unavailable",
                loc=["method"],
                input=data.method,
            )
        bank = await self.banks.get_by_id(card.bank_id)
        final_amount = data.amount
        code = None
        payment_id = None
        if mode is PaymentMode.AUTO:
            reservation = await self.payments.reserve_auto(
                data.amount, settings.digits
            )
            if reservation.transfer_amount is None:
                raise DepositInvoiceUnavailable()
            final_amount = reservation.transfer_amount
            code = reservation.confirmation_code
            payment_id = reservation.id
        payment = CardPayment(
            final_amount=final_amount,
            mode=mode,
            card_number=card.card_number,
            holder_name=card.holder_name,
            bank_id=bank.id,
            bank_title=bank.title,
            bank_icon_url=bank.icon_url,
            confirmation_code=code,
            payment_id=payment_id,
        )
        invoice = await self.deposits.create(customer_id, data.amount, payment)
        return invoice
