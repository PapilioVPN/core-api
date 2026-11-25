"""Gateway account fields returned by the panel API."""

from papilio.schemas.outputs import BaseOutput


class GatewayOutput(BaseOutput):
    id: int
    kind: str
    title: str
    icon_url: str | None
    is_active: bool
