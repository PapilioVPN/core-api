"""Credential-free connection settings for the panel."""

from dataclasses import dataclass
from typing import Self

from ..errors import ConfigUnavailable
from ..models.configs import GatewayConfigModel


@dataclass(frozen=True, slots=True)
class GatewayConfigView:
    gateway_id: int
    kind: str
    api_url: str
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
            has_api_key=bool(record.config.get("api_key")),
            has_ipn_secret=bool(record.config.get("ipn_secret")),
        )
