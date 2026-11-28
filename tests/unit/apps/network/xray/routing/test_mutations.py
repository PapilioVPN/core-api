"""Keep an unconfirmed request distinct from a definite routing rejection."""

from datetime import timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from grpc import StatusCode
from grpc.aio import AioRpcError, Metadata
from papilio.utils.dates import utc_now

from src.apps.network.nodes.infra.grpc.channels import NodeChannels
from src.apps.network.xray.routing.domain.dtos.mutations import ClearBalancer
from src.apps.network.xray.routing.domain.enums.operation import (
    RoutingAction,
    RoutingFailure,
    RoutingState,
)
from src.apps.network.xray.routing.domain.results.operation import (
    RoutingOutcome,
    RoutingPayload,
    RoutingTarget,
)
from src.apps.network.xray.routing.infra.grpc import mutations

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("code", "state", "reason"),
    [
        (StatusCode.ABORTED, RoutingState.UNKNOWN, RoutingFailure.UNCONFIRMED),
        (
            StatusCode.DEADLINE_EXCEEDED,
            RoutingState.UNKNOWN,
            RoutingFailure.TIMEOUT,
        ),
        (
            StatusCode.FAILED_PRECONDITION,
            RoutingState.FAILED,
            RoutingFailure.FENCED,
        ),
    ],
)
async def test_clear_override_preserves_presence_and_does_not_retry(
    monkeypatch: pytest.MonkeyPatch,
    code: StatusCode,
    state: RoutingState,
    reason: RoutingFailure,
) -> None:
    call = AsyncMock(side_effect=AioRpcError(code, Metadata(), Metadata()))
    monkeypatch.setattr(
        mutations,
        "XrayRoutingServiceStub",
        Mock(return_value=Mock(OverrideBalancerTarget=call)),
    )
    gateway = mutations.XrayRoutingGateway(Mock(spec=NodeChannels))
    target = RoutingTarget(
        1,
        "edge",
        "localhost",
        8081,
        RoutingAction.CLEAR,
        utc_now() + timedelta(seconds=15),
        RoutingPayload("", ""),
    )

    outcome = await gateway.mutate(target, ClearBalancer(tag="pool"))

    assert outcome == RoutingOutcome(state, reason)
    call.assert_awaited_once_with(
        mutations.wire.XrayOverrideBalancerTargetRequest(
            id="edge", tag="pool", target=""
        ),
        timeout=2,
    )
