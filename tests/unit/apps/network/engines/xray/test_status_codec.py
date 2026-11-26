"""Distinguish actual Xray state from an unreliable observation."""

import pytest

from src.apps.network.engines.xray.domain.enums.status import XrayInstanceState
from src.apps.network.engines.xray.infra.grpc.codec import decode_instance
from src.apps.network.engines.xray.infra.grpc.v1.instances_pb2 import (
    XrayInstanceState as WireState,
)
from src.apps.network.engines.xray.infra.grpc.v1.instances_pb2 import (
    XrayInstanceStatus,
)

pytestmark = pytest.mark.unit


def test_failed_engine_is_an_observation_without_a_digest() -> None:
    reply = XrayInstanceStatus(
        id="edge", state=WireState.XRAY_INSTANCE_STATE_FAILED
    )
    observation = decode_instance(reply, "edge")
    assert observation is not None
    assert observation.state is XrayInstanceState.FAILED
    assert observation.applied_config_sha256 is None
    assert observation.xray_version is None


@pytest.mark.parametrize(
    "reply",
    [
        XrayInstanceStatus(
            id="edge", state=WireState.XRAY_INSTANCE_STATE_UNSPECIFIED
        ),
        XrayInstanceStatus(
            id="other", state=WireState.XRAY_INSTANCE_STATE_READY
        ),
        XrayInstanceStatus(
            id="edge",
            state=WireState.XRAY_INSTANCE_STATE_STOPPED,
            applied_config_sha256="a" * 64,
        ),
        XrayInstanceStatus(
            id="edge",
            state=WireState.XRAY_INSTANCE_STATE_READY,
            applied_config_sha256="not-a-digest",
        ),
    ],
)
def test_inconsistent_status_does_not_pass_as_observed(
    reply: XrayInstanceStatus,
) -> None:
    assert decode_instance(reply, "edge") is None
