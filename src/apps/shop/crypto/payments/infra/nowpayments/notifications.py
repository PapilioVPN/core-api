"""Verify the signed NOWPayments transport and decode settled invoices."""

from pydantic import JsonValue, ValidationError

from ...domain.errors import InvalidNotification
from ...domain.policy import USD, invoice_mismatch
from ...domain.results.settlement import PaidInvoice, Settlement
from .ipn import verify
from .schemas import NotificationStatus, NowPayment


class NowPaymentsNotification:
    def decode(
        self,
        gateway_id: int,
        data: dict[str, JsonValue],
        signature: str,
        secret: str,
    ) -> PaidInvoice | None:
        """Authenticate the unchanged provider body and extract paid evidence.

        Args:
            gateway_id: The account targeted by the callback.
            data: Unmodified signed notification fields.
            signature: The notification's hexadecimal HMAC.
            secret: The account's IPN secret.

        Returns:
            Fully paid USD invoice evidence, or None for a nonfinal status.

        Raises:
            UnAuthorizedException: The signature is invalid.
            ConflictException: Finished evidence is incomplete or underpaid.
        """
        if not verify(data, signature, secret):
            raise InvalidNotification()
        paid = None
        if data.get("payment_status") == NotificationStatus.FINISHED:
            try:
                notice = NowPayment.model_validate(data)
            except ValidationError:
                raise invoice_mismatch(gateway_id) from None
            currency = notice.price_currency.upper()
            if currency != USD or notice.actually_paid < notice.pay_amount:
                raise invoice_mismatch(gateway_id)
            paid = PaidInvoice(
                settlement=Settlement(
                    notice.order_id, notice.invoice_id, notice.payment_id
                ),
                amount=notice.price_amount,
                currency=currency,
            )
        return paid
