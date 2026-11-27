"""Verify the signed NOWPayments transport and decode settled invoices."""

from pydantic import JsonValue, ValidationError

from ...domain.policy import USD
from ...domain.results.records import PaymentFailure
from ...domain.results.settlement import PaidInvoice, Settlement
from .ipn import verify
from .schemas import NotificationStatus, NowPayment


class NowPaymentsNotification:
    def decode(
        self,
        data: dict[str, JsonValue],
        signature: str,
        secret: str,
    ) -> PaidInvoice | PaymentFailure | None:
        """Authenticate the unchanged provider body and extract paid evidence.

        Args:
            data: Unmodified signed notification fields.
            signature: The notification's hexadecimal HMAC.
            secret: The account's IPN secret.

        Returns:
            Paid invoice evidence, None for nonfinal status, or a failure.
        """
        result: PaidInvoice | PaymentFailure | None = None
        if not verify(data, signature, secret):
            result = PaymentFailure.INVALID_NOTIFICATION
        elif data.get("payment_status") == NotificationStatus.FINISHED:
            result = PaymentFailure.INVOICE_MISMATCH
            try:
                notice = NowPayment.model_validate(data)
            except ValidationError:
                pass
            else:
                currency = notice.price_currency.upper()
                if (
                    currency == USD
                    and notice.actually_paid >= notice.pay_amount
                ):
                    result = PaidInvoice(
                        settlement=Settlement(
                            notice.order_id,
                            notice.invoice_id,
                            notice.payment_id,
                        ),
                        amount=notice.price_amount,
                        currency=currency,
                    )
        return result
