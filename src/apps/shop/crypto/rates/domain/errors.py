"""Report an unusable exchange-rate response."""

from http import HTTPStatus

from papilio.errors.base import APPException
from papilio.errors.outputs import BaseErrorOut


class RateUnavailable(APPException[BaseErrorOut]):
    def __init__(self) -> None:
        super().__init__(
            "The exchange rate is unavailable.",
            "crypto_rate_unavailable",
            HTTPStatus.BAD_GATEWAY,
        )

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )
