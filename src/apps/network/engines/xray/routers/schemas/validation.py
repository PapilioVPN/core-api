"""Panel representation of a candidate validation, not of applied state."""

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.validation import XrayIssueCode, XrayValidationStatus


class XrayValidationIssueOutput(BaseOutput):
    code: XrayIssueCode
    line: int | None
    column: int | None


class XrayConfigValidationOutput(BaseOutput):
    node_id: int
    instance_id: str
    config_sha256: str
    status: XrayValidationStatus
    issue: XrayValidationIssueOutput | None
