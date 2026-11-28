"""Typed metadata from a single saved revision's declared inbounds."""

from dataclasses import dataclass

from ..enums.inbounds import XrayRevisionInboundFailure


@dataclass(frozen=True, slots=True)
class XrayRevisionInbound:
    tag: str
    protocol: str
    network: str | None
    security: str | None


@dataclass(frozen=True, slots=True)
class XrayRevisionInbounds:
    items: tuple[XrayRevisionInbound, ...] = ()
    failure: XrayRevisionInboundFailure | None = None
