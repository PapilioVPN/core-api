"""Preserve Xray issue locations and reject uncorrelated replies."""

import pytest

from src.apps.network.xray.validation.domain.enums.dry_run import (
    XrayIssueCode,
    XrayValidationStatus,
)
from src.apps.network.xray.validation.domain.results.dry_run import (
    XrayValidationIssue,
)
from src.apps.network.xray.validation.infra.grpc.codec import decode_validation
from src.apps.network.xray.validation.infra.grpc.v1.configs_pb2 import (
    XrayConfigIssueCode,
    XrayConfigValidation,
    XrayConfigValidationIssue,
)

pytestmark = pytest.mark.unit


def test_issue_preserves_the_available_location() -> None:
    reply = XrayConfigValidation(
        id="edge",
        issue=XrayConfigValidationIssue(
            code=XrayConfigIssueCode.XRAY_CONFIG_ISSUE_CODE_CONFIG_DECODE_ERROR,
            line=8,
            column=0,
        ),
    )
    decoded = decode_validation(reply, "edge")
    assert decoded.status is XrayValidationStatus.INVALID
    assert decoded.issue == XrayValidationIssue(
        XrayIssueCode.CONFIG_DECODE_ERROR, line=8, column=None
    )


@pytest.mark.parametrize(
    "reply",
    [
        XrayConfigValidation(id="another-instance", valid=True),
        XrayConfigValidation(id="edge", valid=False),
        XrayConfigValidation(
            id="edge", valid=True, issue=XrayConfigValidationIssue(line=2)
        ),
    ],
)
def test_uncorrelated_or_inconsistent_reply_is_not_validation(
    reply: XrayConfigValidation,
) -> None:
    decoded = decode_validation(reply, "edge")
    assert decoded.status is XrayValidationStatus.FAILED
    assert decoded.issue is None
