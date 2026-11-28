"""Publish only the identity of a newly recorded bank transfer."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class TransferCreated(BaseDTO):
    transfer_id: IdType
