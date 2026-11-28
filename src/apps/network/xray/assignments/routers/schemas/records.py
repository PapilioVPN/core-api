"""Separate desired intent from each live Xray observation."""

from datetime import datetime
from typing import Self

from papilio.schemas.outputs import BaseOutput

from src.apps.network.xray.instances.routers.schemas.status import (
    XrayStatusOutput,
)

from ...domain.enums.comparison import XrayRevisionComparisonState
from ...domain.results.records import XrayRevisionComparison


class XrayDesiredRevisionOutput(BaseOutput):
    revision_id: int
    config_sha256: str
    updated_at: datetime | None


class XrayAssignmentOutput(BaseOutput):
    node_id: int
    instance_id: str
    desired: XrayDesiredRevisionOutput | None


class XrayRevisionComparisonOutput(XrayAssignmentOutput):
    state: XrayRevisionComparisonState
    observed: XrayStatusOutput | None

    @classmethod
    def from_comparison(
        cls, node_id: int, instance_id: str, result: XrayRevisionComparison
    ) -> Self:
        """Preserve the native observation alongside the comparison verdict."""
        return cls(
            node_id=node_id,
            instance_id=instance_id,
            state=result.state,
            desired=XrayDesiredRevisionOutput.from_obj(result.desired)
            if result.desired is not None
            else None,
            observed=XrayStatusOutput.from_result(
                node_id, instance_id, result.observed
            )
            if result.observed is not None
            else None,
        )
