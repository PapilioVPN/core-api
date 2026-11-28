"""Protect log stream precision for browser consumers."""

from typing import Self

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.live import XrayLogEnd, XrayLogSource
from ...domain.results.live import XrayLogLine


class XrayLogReadyOutput(BaseOutput):
    node_id: int
    instance_id: str


class XrayLogLineOutput(BaseOutput):
    execution: str
    sequence: str
    received_unix_nano: str
    source: XrayLogSource
    message: str
    truncated: bool
    encoding_replaced: bool
    missed_before: str | None

    @classmethod
    def from_line(cls, line: XrayLogLine) -> Self:
        """Encode the wide integers without JavaScript number rounding."""
        return cls(
            execution=str(line.execution),
            sequence=str(line.sequence),
            received_unix_nano=str(line.received_unix_nano),
            source=line.source,
            message=line.message,
            truncated=line.truncated,
            encoding_replaced=line.encoding_replaced,
            missed_before=str(line.missed_before)
            if line.missed_before is not None
            else None,
        )


class XrayLogEndOutput(BaseOutput):
    status: XrayLogEnd
