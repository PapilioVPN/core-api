"""Publish the identity of a confirmed online payment."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class PaymentConfirmed(BaseDTO):
    payment_id: IdType
