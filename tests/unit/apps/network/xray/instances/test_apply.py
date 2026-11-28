"""Require matching confirmation before reporting a revision as applied."""

from datetime import timedelta
from hashlib import sha256
from unittest.mock import AsyncMock

import pytest
from papilio.utils.dates import utc_now

from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint
from src.apps.network.xray.instances.app.executions.start import (
    XrayStartExecution,
)
from src.apps.network.xray.instances.app.interfaces.start import (
    IXrayStartGateway,
)
from src.apps.network.xray.instances.app.pipelines.start import (
    XrayStartPipeline,
)
from src.apps.network.xray.instances.domain.enums.start import (
    XrayStartReason,
    XrayStartState,
)
from src.apps.network.xray.instances.domain.results.start import (
    XrayStartOutcome,
    XrayStartTarget,
)
from src.apps.network.xray.revisions.domain.results.records import (
    XrayRevisionSource,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("source_available", [True, False])
async def test_apply_requires_source_and_matching_digest(
    source_available: bool,
) -> None:
    source = b'{ "remarks": "revision source" }\n'
    target = XrayStartTarget(
        NodeEndpoint(1, "localhost", 8081, True),
        "edge",
        utc_now() + timedelta(seconds=45),
        2,
    )
    execution = AsyncMock(spec=XrayStartExecution)
    execution.claim.return_value = target
    execution.load_source.return_value = XrayRevisionSource(
        sha256(source).hexdigest(), source
    )
    gateway = AsyncMock(spec=IXrayStartGateway)
    observed_digest = sha256(b"other source").hexdigest()
    gateway.start.return_value = XrayStartOutcome(
        XrayStartState.SUCCEEDED, applied_config_sha256=observed_digest
    )
    if not source_available:
        execution.load_source.return_value = None

    await XrayStartPipeline(execution, gateway).run(3)

    execution.load_source.assert_awaited_once_with(2)
    if source_available:
        gateway.start.assert_awaited_once_with(target, config_json=source)
        expected = XrayStartOutcome(
            XrayStartState.UNKNOWN,
            XrayStartReason.DIGEST_MISMATCH,
            observed_digest,
        )
    else:
        gateway.start.assert_not_awaited()
        expected = XrayStartOutcome(
            XrayStartState.FAILED, XrayStartReason.REVISION_UNAVAILABLE
        )
    execution.finish.assert_awaited_once_with(3, expected)
