"""Report unusable gateway configuration without exposing secrets."""

from http import HTTPStatus

from papilio.errors.base import APPException
from papilio.errors.outputs import BaseErrorOut


class ConfigUnavailable(APPException[BaseErrorOut]):
    def __init__(self) -> None:
        super().__init__(
            "The gateway configuration is unavailable.",
            "crypto_gateway_config_unavailable",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )
