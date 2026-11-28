"""Publish only the identity of the committed routing operation."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class RoutingRequested(BaseDTO):
    operation_id: IdType
