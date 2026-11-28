"""Identities of committed card payment decisions."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class PaymentConfirmed(BaseDTO):
    payment_id: IdType


class PaymentRejected(BaseDTO):
    payment_id: IdType
