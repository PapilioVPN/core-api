"""Admission checks and matching rules for cryptocurrency payments."""

from papilio.errors.exceptions import ConflictException, ValidationException

from src.apps.shop.crypto.gateways.domain.models.records import (
    CryptoGatewayModel,
)

from .models.records import CryptoPaymentModel
from .results.settlement import PaidInvoice

PLISIO = "plisio"
NOWPAYMENTS = "nowpayments"
RIAL = "IRR"
USD = "USD"


def check_amount(gateway: CryptoGatewayModel, amount: int) -> None:
    """Require a gateway that accepts the original amount in rials."""
    if not gateway.is_active:
        raise ValidationException(
            message="This gateway does not accept new payments.",
            message_code="crypto_gateway_inactive",
            loc=["gateway_id"],
            input=gateway.id,
        )
    if (gateway.min_amount is not None and amount < gateway.min_amount) or (
        gateway.max_amount is not None and amount > gateway.max_amount
    ):
        raise ValidationException(
            message="The amount is outside this gateway's limits.",
            message_code="crypto_payment_amount_out_of_bounds",
            loc=["amount"],
            input=amount,
        )


def check_invoice(
    gateway_id: int, payment: CryptoPaymentModel, evidence: PaidInvoice
) -> None:
    """Require the same issuing account, invoice and original quote."""
    if (
        payment.gateway_id != gateway_id
        or payment.invoice_id != evidence.settlement.invoice_id
        or payment.quote_amount != evidence.amount
        or payment.quote_currency != evidence.currency
    ):
        raise invoice_mismatch(gateway_id)


def invoice_mismatch(gateway_id: int) -> ConflictException:
    """Report that a finished notification does not identify a full invoice."""
    return ConflictException(
        message="The notification does not match a full invoice payment.",
        message_code="nowpayments_invoice_mismatch",
        unique_dict={"gateway_id": gateway_id},
    )
