"""Report the confirmed Stop phase of a tracked Xray restart."""

from datetime import datetime

from .apply import XrayApplyOutput


class XrayRestartOutput(XrayApplyOutput):
    stopped_at: datetime | None
