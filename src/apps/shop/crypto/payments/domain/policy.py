"""Admission checks and matching rules for cryptocurrency payments."""

from papilio.errors.exceptions import ValidationException

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


def matches_invoice(
    gateway_id: int, payment: CryptoPaymentModel, evidence: PaidInvoice
) -> bool:
    """Match the issuing account, invoice and frozen quote."""
    return (
        payment.gateway_id == gateway_id
        and payment.invoice_id == evidence.settlement.invoice_id
        and payment.quote_amount == evidence.amount
        and payment.quote_currency == evidence.currency
    )
