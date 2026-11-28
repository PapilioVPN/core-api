"""Typed metadata from a single saved revision's declared inbounds."""

from dataclasses import dataclass

from ..enums.inbounds import XrayRevisionInboundFailure
from .records import XraySourceFailure


@dataclass(frozen=True, slots=True)
class XrayRevisionInbound:
    tag: str
    protocol: str
    network: str | None
    security: str | None


type XrayRevisionInbounds = (
    tuple[XrayRevisionInbound, ...]
    | XrayRevisionInboundFailure
    | XraySourceFailure
)
