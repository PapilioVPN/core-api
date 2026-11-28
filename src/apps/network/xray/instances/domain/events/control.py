"""Identity-only request for a committed Xray lifecycle operation."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class XrayControlRequested(BaseDTO):
    operation_id: IdType
