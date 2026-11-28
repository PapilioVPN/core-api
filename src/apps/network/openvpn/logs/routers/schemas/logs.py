"""OpenVPN log replay batches sent to the Panel."""

from papilio.schemas.outputs import BaseOutput

from src.apps.network.nodes.observations.routers.schemas.observation import (
    UInt64Text,
)


class OpenVPNLogLineOutput(BaseOutput):
    sequence: UInt64Text
    timestamp_unix_seconds: UInt64Text
    level: str
    message: str


class OpenVPNLogBatchOutput(BaseOutput):
    execution_id: str
    dropped: UInt64Text
    entries: tuple[OpenVPNLogLineOutput, ...]
