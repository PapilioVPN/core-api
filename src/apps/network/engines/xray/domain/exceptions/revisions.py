"""Report unusable revision source without exposing secrets."""

from http import HTTPStatus

from papilio.errors.base import APPException
from papilio.errors.outputs import BaseErrorOut


class XrayRevisionSourceUnavailable(APPException[BaseErrorOut]):
    def __init__(self) -> None:
        super().__init__(
            "The Xray revision source is unavailable.",
            "xray_revision_source_unavailable",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def as_schema(self) -> BaseErrorOut:
        return BaseErrorOut(
            message=self.message, message_code=self.message_code
        )
