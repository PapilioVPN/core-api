"""Bound the explicit Xray instance selection for a live comparison."""

from papilio.schemas.inputs import BaseDTO

from src.apps.network.xray.instances.domain.dtos.identity import (
    XrayInstanceTargets,
)


class XrayFleetComparisonInput(BaseDTO):
    targets: XrayInstanceTargets
