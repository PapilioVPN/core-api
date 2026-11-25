"""Connection settings the panel can read without credentials."""

from papilio.schemas.outputs import BaseOutput

from ...domain.dtos.configs import PriceCurrency


class GatewayConfigOutput(BaseOutput):
    gateway_id: int
    kind: str
    api_url: str
    price_currency: PriceCurrency
    has_api_key: bool
    has_ipn_secret: bool
