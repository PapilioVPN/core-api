"""Report provider failures without leaking the request or credentials."""

from http import HTTPStatus

from papilio.errors.base import APPException
from papilio.errors.exceptions import UnAuthorizedException
from papilio.errors.outputs import BaseErrorOut


class InvoiceUnavailable(APPException[BaseErrorOut]):
    def __init__(self) -> None:
        super().__init__(
            "The payment gateway did not return a usable invoice.",
            "crypto_invoice_unavailable",
            HTTPStatus.BAD_GATEWAY,
        )

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )


class CheckUnavailable(APPException[BaseErrorOut]):
    def __init__(self) -> None:
        super().__init__(
            "The payment gateway could not be checked.",
            "crypto_payment_check_unavailable",
            HTTPStatus.BAD_GATEWAY,
        )

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )


class InvalidNotification(UnAuthorizedException):
    def __init__(self) -> None:
        super().__init__(
            message="Invalid NOWPayments notification signature.",
            message_code="nowpayments_signature_invalid",
        )
