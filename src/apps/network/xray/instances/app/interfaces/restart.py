"""Accept a revision-backed Xray restart."""

from typing import Protocol
from uuid import UUID

from ...domain.models.start import XrayStartModel


class IXrayRestartCommand(Protocol):
    async def restart(
        self,
        node_id: int,
        instance_id: str,
        revision_id: int,
        request_key: UUID,
    ) -> XrayStartModel: ...
