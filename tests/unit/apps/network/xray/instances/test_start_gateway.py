"""Check evidence and retry behavior at the Xray lifecycle boundary."""

from datetime import timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from grpc import StatusCode
from grpc.aio import AioRpcError, Metadata
from papilio.utils.dates import utc_now

from src.apps.network.nodes.infra.grpc.channels import NodeChannels
from src.apps.network.xray.instances.domain.enums.start import (
    XrayStartReason,
    XrayStartState,
)
from src.apps.network.xray.instances.domain.results.start import (
    XrayStartOutcome,
    XrayStartTarget,
)
from src.apps.network.xray.instances.infra.grpc.start import XrayStartGateway
from src.apps.network.xray.instances.infra.grpc.v1.instances_pb2 import (
    XrayInstanceRequest,
    XrayInstanceState,
    XrayInstanceStatus,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("code", "state", "reason"),
    [
        (None, XrayStartState.UNKNOWN, XrayStartReason.UNCONFIRMED),
        (
            StatusCode.DEADLINE_EXCEEDED,
            XrayStartState.UNKNOWN,
            XrayStartReason.TIMEOUT,
        ),
        (
            StatusCode.UNAVAILABLE,
            XrayStartState.UNKNOWN,
            XrayStartReason.UNAVAILABLE,
        ),
        (
            StatusCode.NOT_FOUND,
            XrayStartState.FAILED,
            XrayStartReason.INSTANCE_NOT_FOUND,
        ),
    ],
)
async def test_start_requires_confirmed_digest(
    monkeypatch: pytest.MonkeyPatch,
    code: StatusCode | None,
    state: XrayStartState,
    reason: XrayStartReason,
) -> None:
    incomplete = XrayInstanceStatus(
        id="edge", state=XrayInstanceState.XRAY_INSTANCE_STATE_READY
    )
    start = AsyncMock(return_value=incomplete)
    if code is not None:
        start.side_effect = AioRpcError(code, Metadata(), Metadata())
    monkeypatch.setattr(
        "src.apps.network.xray.instances.infra.grpc.start.XrayInstancesServiceStub",
        Mock(return_value=Mock(Start=start)),
    )
    gateway = XrayStartGateway(Mock(spec=NodeChannels))
    target = XrayStartTarget(
        1, "edge", "localhost", 8081, utc_now() + timedelta(seconds=45)
    )

    outcome = await gateway.start(target)

    assert outcome == XrayStartOutcome(state, reason)
    start.assert_awaited_once_with(XrayInstanceRequest(id="edge"), timeout=20)
