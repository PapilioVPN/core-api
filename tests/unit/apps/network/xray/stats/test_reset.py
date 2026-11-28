"""Verify rich status details without inventing counter effects."""

import pytest
from google.protobuf.message import Message
from google.rpc.status_pb2 import Status
from grpc import StatusCode
from grpc.aio import AioRpcError, Metadata

from src.apps.network.xray.stats.domain.enums.reset import (
    ResetEffect,
    ResetReason,
    ResetState,
)
from src.apps.network.xray.stats.infra.grpc.reset_codec import (
    decode_failure,
    decode_scope,
)
from src.apps.network.xray.stats.infra.grpc.v1 import traffic_pb2 as wire

pytestmark = pytest.mark.unit


def _rpc_error(code: StatusCode, detail: Message) -> AioRpcError:
    status = Status(code=code.value[0])
    status.details.add().Pack(detail)
    metadata = Metadata(
        ("grpc-status-details-bin", status.SerializeToString())
    )
    return AioRpcError(code, Metadata(), metadata)


@pytest.mark.parametrize(
    ("code", "effect", "state", "reason", "counter_effect"),
    [
        (
            StatusCode.ABORTED,
            wire.XrayTrafficDirectionReset.NOT_APPLIED,
            ResetState.PARTIAL,
            ResetReason.INTERRUPTED,
            ResetEffect.NOT_APPLIED,
        ),
        (
            StatusCode.UNKNOWN,
            wire.XrayTrafficDirectionReset.UNKNOWN,
            ResetState.UNKNOWN,
            ResetReason.UNCONFIRMED,
            ResetEffect.UNKNOWN,
        ),
    ],
)
def test_pair_error_preserves_confirmed_bytes_next_to_failure(
    code: StatusCode,
    effect: wire.XrayTrafficDirectionReset.Effect,
    state: ResetState,
    reason: ResetReason,
    counter_effect: ResetEffect,
) -> None:
    evidence = wire.XrayTrafficPairResetResult(
        uplink=wire.XrayTrafficDirectionReset(
            effect=wire.XrayTrafficDirectionReset.ACKNOWLEDGED,
            previous_bytes=0,
        ),
        downlink=wire.XrayTrafficDirectionReset(effect=effect),
    )
    result = decode_failure(_rpc_error(code, evidence), "native/edge")
    assert result.state is state
    assert result.reason is reason
    assert result.counters[0]["previous_bytes"] == 0
    assert result.counters[1]["previous_bytes"] is None
    assert result.counters[1]["effect"] is counter_effect


def test_failure_without_effect_never_implies_reset_was_not_applied() -> None:
    error = AioRpcError(StatusCode.DEADLINE_EXCEEDED, Metadata(), Metadata())
    result = decode_failure(error, None)
    assert result.state is ResetState.UNKNOWN
    assert result.reason is ResetReason.TIMEOUT
    assert result.counters == ()


def test_scope_report_retains_order_and_limit_fence() -> None:
    reply = wire.XrayTrafficScopeResetResult(
        outcome=wire.XrayTrafficScopeResetResult.INTERRUPTED,
        counters=[
            wire.XrayTrafficScopedCounterReset(
                name="z",
                direction=wire.XRAY_TRAFFIC_DIRECTION_UPLINK,
                result=wire.XrayTrafficDirectionReset(
                    effect=wire.XrayTrafficDirectionReset.ACKNOWLEDGED,
                    previous_bytes=10,
                ),
            ),
            wire.XrayTrafficScopedCounterReset(
                name="a",
                direction=wire.XRAY_TRAFFIC_DIRECTION_DOWNLINK,
                result=wire.XrayTrafficDirectionReset(
                    effect=wire.XrayTrafficDirectionReset.NOT_ATTEMPTED,
                ),
            ),
        ],
    )
    report = decode_scope(reply, 2)
    assert report.state is ResetState.PARTIAL
    assert [row["name"] for row in report.counters] == ["z", "a"]
    assert decode_scope(reply, 1).state is ResetState.UNKNOWN
