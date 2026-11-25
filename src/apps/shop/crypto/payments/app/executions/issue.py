"""Read a frozen payment and attach its hosted invoice in short SQL scopes."""

from dishka import AsyncContainer
from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    IPlisioConfigQuery,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)

from ...domain.results.invoice import Invoice, PlisioIssue
from ..interfaces.services import ICryptoPaymentService


class PaymentIssueExecution:
    def __init__(self, container: AsyncContainer) -> None:
        """Bind the native container for the short SQL phases."""
        self.container = container

    @request_scoped
    @transactional
    async def prepare(
        self,
        id: int,
        *,
        payments: ICryptoPaymentService = Inject(),
        gateways: ICryptoGatewayService = Inject(),
        configs: IPlisioConfigQuery = Inject(),
    ) -> PlisioIssue | Invoice:
        """Prepare issuance using the frozen amount and currency.

        Args:
            id: Payment identity.
            payments: The payment service injected for this phase.
            gateways: The account service injected for this phase.
            configs: The internal Plisio settings reader.

        Returns:
            The saved invoice or the inputs for a provider call.

        Raises:
            ConflictException: The payment or gateway cannot issue an invoice.
            ConfigUnavailable: The gateway credentials cannot be read.
        """
        payment = await payments.get_by_id(id)
        if payment.invoice_id is not None and payment.invoice_url is not None:
            result = Invoice(id=payment.invoice_id, url=payment.invoice_url)
        else:
            amount, currency = payment.quote_amount, payment.quote_currency
            if amount is None or (currency != "IRR" and currency != "USD"):
                raise ConflictException(
                    message="The payment must be quoted before issuance.",
                    message_code="crypto_payment_unquoted",
                    unique_dict={"payment_id": id},
                )
            gateway = await gateways.get_by_id(payment.gateway_id)
            if gateway.kind != "plisio" or not gateway.is_active:
                raise ConflictException(
                    message="The gateway cannot issue a Plisio invoice.",
                    message_code="crypto_gateway_issue_unavailable",
                    unique_dict={"gateway_id": gateway.id},
                )
            config = await configs.get(gateway.id)
            result = PlisioIssue(
                payment_id=id, amount=amount, currency=currency, config=config
            )
        return result

    @request_scoped
    @transactional
    async def complete(
        self,
        id: int,
        data: Invoice,
        *,
        payments: ICryptoPaymentService = Inject(),
    ) -> Invoice:
        """Save the invoice returned by Plisio and return the stored result.

        Args:
            id: Payment identity handed to the provider.
            data: Provider invoice identity and hosted URL.
            payments: The payment service injected for the write.

        Returns:
            The original stored invoice, including on a concurrent replay.

        Raises:
            ConflictException: Another invoice was recorded for the payment.
        """
        payment = await payments.set_invoice(id, data)
        if payment is None:
            payment = await payments.get_by_id(id)
        if payment.invoice_id != data.id or payment.invoice_url is None:
            raise ConflictException(
                message="The returned invoice does not match the payment.",
                message_code="crypto_payment_invoice_mismatch",
                unique_dict={"payment_id": id},
            )
        return Invoice(id=data.id, url=payment.invoice_url)
