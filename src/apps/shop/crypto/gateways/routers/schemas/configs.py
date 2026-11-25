"""Connection settings the panel can read without credentials."""

from papilio.schemas.outputs import BaseOutput


class GatewayConfigOutput(BaseOutput):
    gateway_id: int
    kind: str
    api_url: str
    has_api_key: bool
    has_ipn_secret: bool
