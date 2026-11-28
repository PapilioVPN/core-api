"""Expose account metadata and only the displayable provider options."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.records import GatewayKind


class GatewayOutput(BaseOutput):
    id: int
    kind: GatewayKind
    title: str
    icon_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
