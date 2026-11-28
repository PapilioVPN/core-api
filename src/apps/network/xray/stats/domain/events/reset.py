"""Publish only the identity of the committed traffic reset operation."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class TrafficResetRequested(BaseDTO):
    operation_id: IdType
