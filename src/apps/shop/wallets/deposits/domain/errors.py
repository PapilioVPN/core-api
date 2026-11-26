"""Report that an invoice could not be saved or loaded."""

from http import HTTPStatus

from papilio.errors.base import APPException
from papilio.errors.outputs import BaseErrorOut


class DepositInvoiceUnavailable(APPException[BaseErrorOut]):
    def __init__(self) -> None:
        super().__init__(
            "The wallet top-up invoice is unavailable.",
            "wallet_deposit_invoice_unavailable",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )
