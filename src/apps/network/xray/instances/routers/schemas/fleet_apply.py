"""Panel rows for fleet Apply admission and independent tracking."""

from typing import Self

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.fleet import XrayFleetOperationStatus
from ...domain.results.fleet import XrayFleetOperationResult
from .apply import XrayApplyOutput


class XrayFleetApplyOutput(BaseOutput):
    node_id: int
    instance_id: str
    status: XrayFleetOperationStatus
    operation_id: int | None
    operation: XrayApplyOutput | None

    @classmethod
    def from_result(cls, row: XrayFleetOperationResult) -> Self:
        """Expose an accepted operation or a credential-free target failure."""
        return cls(
            node_id=row.node_id,
            instance_id=row.instance_id,
            status=row.status,
            operation_id=row.operation_id,
            operation=XrayApplyOutput.from_obj(row.operation)
            if row.operation is not None
            else None,
        )
