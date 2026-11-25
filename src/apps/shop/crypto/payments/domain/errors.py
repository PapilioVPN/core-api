"""Sanitized payment gateway errors."""

from http import HTTPStatus

from papilio.errors.base import APPException
from papilio.errors.outputs import BaseErrorOut


class GatewayUnavailable(APPException[BaseErrorOut]):
    def __init__(
        self, *, configured: bool = True, payment_id: int | None = None
    ) -> None:
        super().__init__(
            "The payment gateway is unavailable.",
            "crypto_gateway_unavailable",
            HTTPStatus.BAD_GATEWAY
            if configured
            else HTTPStatus.SERVICE_UNAVAILABLE,
        )

        self.payment_id = payment_id

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )
