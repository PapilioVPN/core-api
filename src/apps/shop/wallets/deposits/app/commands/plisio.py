"""Issue a hosted Plisio invoice for a wallet top-up."""

from datetime import timedelta

from papilio.errors.exceptions import ValidationException
from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now

from src.apps.shop.crypto.gateways.app.interfaces.queries import (
    IGatewayMethodsQuery,
)
from src.apps.shop.crypto.gateways.domain.results.methods import GatewayOption
from src.apps.shop.crypto.payments.app.interfaces.commands import (
    IPaymentCreateCommand,
    IPaymentQuoteCommand,
)
from src.apps.shop.crypto.payments.app.interfaces.issue import (
    IPaymentIssuePipeline,
)
from src.apps.shop.crypto.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.crypto.payments.domain.errors import InvoiceUnavailable
from src.apps.shop.crypto.payments.domain.models.records import (
    CryptoPaymentModel,
)
from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)

from ...domain.dtos.records import PlisioDeposit
from ...domain.models.records import DepositInvoice, PlisioPayment
from ..interfaces.services import IWalletDepositService
from ..policy import INVOICE_TTL

RATE_MAX_AGE = timedelta(minutes=2)


class PlisioInvoiceCommand:
    def __init__(
        self,
        customers: ICustomerService,
        gateways: IGatewayMethodsQuery,
        create: IPaymentCreateCommand,
        quote: IPaymentQuoteCommand,
        issuer: IPaymentIssuePipeline,
        deposits: IWalletDepositService,
    ) -> None:
        """Bind customer, gateway, crypto payment and wallet invoice owners."""
        self.customers = customers
        self.gateways = gateways
        self.create = create
        self.quote = quote
        self.issuer = issuer
        self.deposits = deposits

    async def issue(
        self, customer_id: int, data: PlisioDeposit
    ) -> DepositInvoice:
        """Issue the selected hosted invoice and store its payment details.

        Args:
            customer_id: Identity of the customer requesting the top-up.
            data: Selected gateway and original amount in whole rials.

        Returns:
            The cached wallet invoice with its hosted URL and deadline.

        Raises:
            NotFoundException: The customer does not exist.
            ValidationException: The gateway is unavailable for this amount.
            RateUnavailable: The USD quote needs a fresh exchange rate.
            InvoiceUnavailable: The quote or hosted invoice is unusable.
            DepositInvoiceUnavailable: The wallet invoice could not be stored.
        """
        gateway, payment = await self._prepare(customer_id, data)
        amount, currency = payment.quote_amount, payment.quote_currency
        if amount is None or currency not in ("IRR", "USD"):
            raise InvoiceUnavailable()

        created_at = utc_now()
        hosted = await self.issuer.issue(
            payment.id,
            expire_minutes=INVOICE_TTL // timedelta(minutes=1),
        )
        details = PlisioPayment(
            gateway_id=gateway.id,
            gateway_title=gateway.title,
            gateway_icon_url=gateway.icon_url,
            final_amount=amount,
            currency=currency,
            invoice_url=hosted.url,
            payment_id=payment.id,
        )
        invoice = await self.deposits.create(
            customer_id, data.amount, details, created_at=created_at
        )
        return invoice

    @transactional
    async def _prepare(
        self, customer_id: int, data: PlisioDeposit
    ) -> tuple[GatewayOption, CryptoPaymentModel]:
        """Validate the selected account and commit the local frozen quote."""
        await self.customers.get_by_id(customer_id)
        gateway = await self.gateways.find(data.gateway_id, data.amount)
        if gateway is None:
            raise ValidationException(
                message="This gateway is unavailable for the selected amount.",
                message_code="deposit_gateway_unavailable",
                loc=["gateway_id"],
                input=data.gateway_id,
            )
        payment = await self.create.create(
            PaymentCreate(gateway_id=gateway.id, amount=data.amount)
        )
        quoted = await self.quote.quote(payment.id, max_age=RATE_MAX_AGE)
        return gateway, quoted
