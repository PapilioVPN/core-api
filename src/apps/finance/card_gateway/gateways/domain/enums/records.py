"""Supported hosted card transfer providers."""

from enum import StrEnum


class GatewayKind(StrEnum):
    VARIZA = "variza"
