"""Connection metadata and expected configuration failures."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from ..dtos.configs import PriceCurrency
from ..models.configs import GatewayConfigModel


class ConfigFailure(StrEnum):
    UNAVAILABLE = "config_unavailable"


def plisio_currency(
    record: GatewayConfigModel | None,
) -> PriceCurrency | ConfigFailure:
    """Read an account's selected currency, defaulting to IRR."""
    value = record.config.get("price_currency", "IRR") if record else "IRR"
    result: PriceCurrency | ConfigFailure = ConfigFailure.UNAVAILABLE
    if isinstance(value, str) and (value == "IRR" or value == "USD"):
        result = value
    return result


@dataclass(frozen=True, slots=True)
class GatewayConfigView:
    gateway_id: int
    kind: str
    api_url: str
    price_currency: PriceCurrency
    has_api_key: bool
    has_ipn_secret: bool
    callback_url: str | None = None

    @classmethod
    def from_record(
        cls, record: GatewayConfigModel, kind: str
    ) -> Self | ConfigFailure:
        """Read displayable settings without exposing encrypted credentials."""
        result: Self | ConfigFailure = ConfigFailure.UNAVAILABLE
        api_url = record.config.get("api_url")
        currency = plisio_currency(record) if kind == "plisio" else "USD"
        if isinstance(api_url, str) and not isinstance(
            currency, ConfigFailure
        ):
            callback_url = record.config.get("callback_url")
            result = cls(
                gateway_id=record.gateway_id,
                kind=kind,
                api_url=api_url,
                price_currency=currency,
                has_api_key=bool(record.config.get("api_key")),
                has_ipn_secret=bool(record.config.get("ipn_secret")),
                callback_url=callback_url
                if isinstance(callback_url, str)
                else None,
            )
        return result
