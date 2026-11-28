"""Accept one explicit Xray revision application."""

from typing import Protocol
from uuid import UUID

from ...domain.models.start import XrayStartModel


class IXrayApplyCommand(Protocol):
    async def apply(
        self,
        node_id: int,
        instance_id: str,
        revision_id: int,
        request_key: UUID,
    ) -> XrayStartModel: ...
