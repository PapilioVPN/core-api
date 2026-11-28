"""Authenticate Variza's raw body and normalize its paid event."""

from hmac import compare_digest, digest
from json import loads
from typing import Annotated

from papilio.errors.exceptions import ValidationException
from papilio.types.constants import INT64_MAX
from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    SecretStr,
)

from ...domain.dtos.paid import PaidTransfer
from .payload import RIALS_PER_TOMAN

type TomanAmount = Annotated[
    int, Field(strict=True, gt=0, le=INT64_MAX // RIALS_PER_TOMAN)
]


class EventPayload(BaseModel):
    event: str


class PaidPayload(EventPayload):
    status: str
    slug: str = Field(min_length=1, max_length=255)
    attempt_code: str = Field(min_length=1, max_length=255)
    base_amount: TomanAmount
    amount: TomanAmount
    sent_at: AwareDatetime


class VarizaWebhookCodec:
    def valid_signature(
        self, body: bytes, signature: str, secret: SecretStr
    ) -> bool:
        """Check the documented HMAC over the exact signed bytes.

        Args:
            body: Raw HTTP body before JSON decoding.
            signature: Provider header with the sha256 prefix and hex digest.
            secret: Exact credential configured for the gateway account.

        Returns:
            Whether the signature matches the raw body.
        """
        key = secret.get_secret_value().encode()
        expected = b"sha256=" + digest(key, body, "sha256").hex().encode()
        return compare_digest(expected, signature.encode())

    def read_paid(self, body: bytes) -> PaidTransfer | None:
        """Read canonical paid evidence after signature verification.

        Args:
            body: Authenticated raw Variza notification.

        Returns:
            Observed transfer amounts normalized to rials, or None for other
            events or statuses.

        Raises:
            ValidationException: The payload does not match the wire contract.
        """
        transfer = None
        try:
            payload = loads(body)
            event = EventPayload.model_validate(payload)
            if event.event == "payment.paid":
                data = PaidPayload.model_validate(payload)
                if data.status == "paid":
                    transfer = PaidTransfer(
                        slug=data.slug,
                        attempt_code=data.attempt_code,
                        base_amount=data.base_amount * RIALS_PER_TOMAN,
                        paid_amount=data.amount * RIALS_PER_TOMAN,
                        sent_at=data.sent_at,
                    )
        except ValueError:
            raise ValidationException(
                message="Invalid Variza notification.",
                message_code="variza_webhook_invalid",
                loc=["body"],
            ) from None
        return transfer
