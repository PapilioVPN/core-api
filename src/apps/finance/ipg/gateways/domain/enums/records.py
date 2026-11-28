"""Supported online payment providers."""

from enum import StrEnum


class GatewayKind(StrEnum):
    ZARINPAL = "zarinpal"
    ZIBAL = "zibal"
