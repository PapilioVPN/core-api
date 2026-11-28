"""Identity-only publication for a committed revision application."""

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType


class XrayApplyRequested(BaseDTO):
    operation_id: IdType
