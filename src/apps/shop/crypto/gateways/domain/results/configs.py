"""Credential-free connection settings for the panel."""

from dataclasses import dataclass
from typing import Self

from ..dtos.configs import PriceCurrency
from ..errors import ConfigUnavailable
from ..models.configs import GatewayConfigModel


def plisio_currency(record: GatewayConfigModel | None) -> PriceCurrency:
    """Read Plisio's pricing currency, with IRR as the default."""
    value = record.config.get("price_currency", "IRR") if record else "IRR"
    if not isinstance(value, str) or (value != "IRR" and value != "USD"):
        raise ConfigUnavailable()
    return value


@dataclass(frozen=True, slots=True)
class GatewayConfigView:
    gateway_id: int
    kind: str
    api_url: str
    price_currency: PriceCurrency
    has_api_key: bool
    has_ipn_secret: bool

    @classmethod
    def from_record(cls, record: GatewayConfigModel, kind: str) -> Self:
        """Return connection metadata without including encrypted values."""
        api_url = record.config.get("api_url")
        if not isinstance(api_url, str):
            raise ConfigUnavailable()
        return cls(
            gateway_id=record.gateway_id,
            kind=kind,
            api_url=api_url,
            price_currency=plisio_currency(record)
            if kind == "plisio"
            else "USD",
            has_api_key=bool(record.config.get("api_key")),
            has_ipn_secret=bool(record.config.get("ipn_secret")),
        )
