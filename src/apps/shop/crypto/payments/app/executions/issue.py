"""Read a frozen payment and attach its hosted invoice in short SQL scopes."""

from dishka import AsyncContainer
from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    INowPaymentsConfigQuery,
    IPlisioConfigQuery,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.results.configs import ConfigFailure

from ...domain.policy import NOWPAYMENTS, PLISIO, RIAL, USD
from ...domain.results.invoice import Invoice, NowPaymentsIssue, PlisioIssue
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
        nowpayments: INowPaymentsConfigQuery = Inject(),
    ) -> PlisioIssue | NowPaymentsIssue | Invoice | ConfigFailure:
        """Prepare issuance using the frozen amount and currency.

        Args:
            id: Payment identity.
            payments: The payment service injected for this phase.
            gateways: The account service injected for this phase.
            configs: The internal Plisio settings reader.
            nowpayments: The internal NOWPayments settings reader.

        Returns:
            The saved invoice or the inputs for a provider call.

        Raises:
            ConflictException: The payment or gateway cannot issue an invoice.
        """
        payment = await payments.get_by_id(id)
        if payment.invoice_id is not None and payment.invoice_url is not None:
            result = Invoice(id=payment.invoice_id, url=payment.invoice_url)
        else:
            amount, currency = payment.quote_amount, payment.quote_currency
            if amount is None or (currency != RIAL and currency != USD):
                raise ConflictException(
                    message="The payment must be quoted before issuance.",
                    message_code="crypto_payment_unquoted",
                    unique_dict={"payment_id": id},
                )
            gateway = await gateways.get_by_id(payment.gateway_id)
            if gateway.is_active and gateway.kind == PLISIO:
                config = await configs.get(gateway.id)
                result = (
                    config
                    if isinstance(config, ConfigFailure)
                    else PlisioIssue(id, amount, currency, config)
                )
            elif (
                gateway.is_active
                and gateway.kind == NOWPAYMENTS
                and currency == USD
            ):
                now_config = await nowpayments.find(gateway.id)
                if isinstance(now_config, ConfigFailure) or now_config is None:
                    result = ConfigFailure.UNAVAILABLE
                else:
                    result = NowPaymentsIssue(id, amount, now_config)
            else:
                raise ConflictException(
                    message="The gateway cannot issue a hosted invoice.",
                    message_code="crypto_gateway_issue_unavailable",
                    unique_dict={"gateway_id": gateway.id},
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
        """Save the hosted invoice returned by the issuing provider.

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
