"""Interpret live evidence without consulting storage or Node."""

from src.apps.network.xray.instances.domain.enums.status import (
    XrayInstanceState,
    XrayStatusCode,
)
from src.apps.network.xray.instances.domain.results.status import (
    XrayStatusResult,
)

from ...domain.enums.comparison import XrayRevisionComparisonState
from ...domain.results.records import (
    XrayDesiredRevision,
    XrayRevisionComparison,
)


def build_comparison(
    desired: XrayDesiredRevision | None, observed: XrayStatusResult | None
) -> XrayRevisionComparison:
    """Distinguish an unassigned target from unavailable evidence."""
    state = XrayRevisionComparisonState.UNKNOWN
    if desired is not None and observed is not None:
        state = compare_revision(desired.config_sha256, observed)
    elif desired is None and observed is None:
        state = XrayRevisionComparisonState.UNASSIGNED
    return XrayRevisionComparison(state, desired, observed)


def compare_revision(
    expected: str, observed: XrayStatusResult
) -> XrayRevisionComparisonState:
    """Only a ready Node with a digest can prove match or drift."""
    state = XrayRevisionComparisonState.UNKNOWN
    current = observed.instance
    if observed.status is XrayStatusCode.OBSERVED and current is not None:
        if current.state is XrayInstanceState.STOPPED:
            state = XrayRevisionComparisonState.STOPPED
        elif (
            current.state is XrayInstanceState.READY
            and current.applied_config_sha256 is not None
        ):
            state = (
                XrayRevisionComparisonState.MATCHED
                if current.applied_config_sha256 == expected
                else XrayRevisionComparisonState.DIFFERENT
            )
    return state
