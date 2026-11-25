"""Report failed exchange-rate reads or refresh requests."""

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


class RefreshUnavailable(APPException[BaseErrorOut]):
    def __init__(self) -> None:
        super().__init__(
            "Rate refresh could not be queued.",
            "crypto_rate_refresh_unavailable",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )
