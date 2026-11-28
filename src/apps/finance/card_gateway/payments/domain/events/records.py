"""Identity of a committed hosted payment confirmation."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class PaymentConfirmed(BaseDTO):
    payment_id: IdType
