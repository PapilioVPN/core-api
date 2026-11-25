"""Report an unavailable authoritative preview store."""

from http import HTTPStatus

from papilio.errors.base import APPException
from papilio.errors.outputs import BaseErrorOut


class InvoiceUnavailable(APPException[BaseErrorOut]):
    def __init__(self) -> None:
        super().__init__(
            "The billing invoice preview store is unavailable.",
            "billing_invoice_unavailable",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )
