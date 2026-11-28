"""Present scoped Xray fleet admission and execution evidence."""

from typing import Self

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.fleet import XrayFleetOperationStatus
from ...domain.results.fleet import XrayFleetOperationResult
from .restart import XrayRestartOutput
from .start import XrayStartOutput


class XrayFleetOperationOutput(BaseOutput):
    node_id: int
    instance_id: str
    status: XrayFleetOperationStatus
    operation_id: int | None
    operation: XrayStartOutput | None

    @classmethod
    def from_result(cls, row: XrayFleetOperationResult) -> Self:
        """Expose the existing execution evidence for an accepted row."""
        return cls(
            node_id=row.node_id,
            instance_id=row.instance_id,
            status=row.status,
            operation_id=row.operation_id,
            operation=XrayStartOutput.from_obj(row.operation)
            if row.operation is not None
            else None,
        )


class XrayFleetRestartOutput(BaseOutput):
    node_id: int
    instance_id: str
    status: XrayFleetOperationStatus
    operation_id: int | None
    operation: XrayRestartOutput | None

    @classmethod
    def from_result(cls, row: XrayFleetOperationResult) -> Self:
        """Report each restart with its independently confirmed Stop phase."""
        return cls(
            node_id=row.node_id,
            instance_id=row.instance_id,
            status=row.status,
            operation_id=row.operation_id,
            operation=XrayRestartOutput.from_obj(row.operation)
            if row.operation is not None
            else None,
        )
