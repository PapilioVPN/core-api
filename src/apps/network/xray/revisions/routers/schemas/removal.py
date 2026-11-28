"""Panel output for each selected Xray revision."""

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.removal import XrayRevisionRemovalStatus


class XrayRevisionRemovalOutput(BaseOutput):
    revision_id: int
    status: XrayRevisionRemovalStatus
