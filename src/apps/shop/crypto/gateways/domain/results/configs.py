"""Credential-free connection settings for the panel."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GatewayConfigView:
    gateway_id: int
    kind: str
    api_url: str
    has_api_key: bool
    has_ipn_secret: bool
