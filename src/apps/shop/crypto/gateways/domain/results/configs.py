"""The panel's credential-free gateway configuration projection."""

from dataclasses import dataclass
from typing import Self

from ..dtos.configs import ConfigWrite, NowPaymentsConfig


@dataclass(frozen=True, slots=True)
class GatewayConfigView:
    gateway_id: int
    kind: str
    api_url: str
    callback_base_url: str
    price_decimals: int
    has_api_key: bool
    has_ipn_secret: bool

    @classmethod
    def from_config(cls, gateway_id: int, config: ConfigWrite) -> Self:
        """Keep URL settings and key presence only."""
        return cls(
            gateway_id=gateway_id,
            kind=config.kind,
            api_url=config.api_url,
            callback_base_url=str(config.callback_base_url),
            price_decimals=config.price_decimals,
            has_api_key=True,
            has_ipn_secret=isinstance(config, NowPaymentsConfig),
        )
