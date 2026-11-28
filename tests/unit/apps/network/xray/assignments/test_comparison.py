"""Only a ready engine with a digest can prove an assignment mismatch."""

import pytest

from src.apps.network.xray.assignments.app.policies.comparison import (
    compare_revision,
)
from src.apps.network.xray.assignments.domain.enums.comparison import (
    XrayRevisionComparisonState,
)
from src.apps.network.xray.instances.domain.enums.status import (
    XrayInstanceState,
    XrayStatusCode,
)
from src.apps.network.xray.instances.domain.results.status import (
    XrayInstanceObservation,
    XrayStatusResult,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "observed",
    [
        XrayStatusResult(XrayStatusCode.TIMEOUT),
        XrayStatusResult(XrayStatusCode.UNAVAILABLE),
        XrayStatusResult(
            XrayStatusCode.OBSERVED,
            XrayInstanceObservation(XrayInstanceState.READY, None, None, None),
        ),
        XrayStatusResult(
            XrayStatusCode.OBSERVED,
            XrayInstanceObservation(
                XrayInstanceState.STARTING, None, None, None
            ),
        ),
    ],
)
def test_inconclusive_observations_are_not_drift(
    observed: XrayStatusResult,
) -> None:
    assert (
        compare_revision("a" * 64, observed)
        is XrayRevisionComparisonState.UNKNOWN
    )
