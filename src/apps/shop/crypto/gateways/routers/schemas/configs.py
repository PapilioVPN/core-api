"""Fields the administrator can read back after saving gateway settings."""

from papilio.schemas.outputs import BaseOutput


class GatewayConfigOutput(BaseOutput):
    gateway_id: int
    kind: str
    api_url: str
    callback_base_url: str
    price_decimals: int
    has_api_key: bool
    has_ipn_secret: bool
