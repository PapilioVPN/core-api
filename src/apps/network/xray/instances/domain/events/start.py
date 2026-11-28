"""Identity-only publication for a committed Xray start operation."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class XrayStartRequested(BaseDTO):
    operation_id: IdType
