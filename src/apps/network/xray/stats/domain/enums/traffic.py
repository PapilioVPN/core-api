"""Xray counter scopes exposed to Network operators."""

from enum import StrEnum


class XrayTrafficScope(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
