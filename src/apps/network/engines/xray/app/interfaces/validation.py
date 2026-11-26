"""Typed contracts for validating a proposal against an Xray instance."""

from typing import Protocol

from ...domain.dtos.validation import XrayConfigCandidate
from ...domain.results.validation import (
    XrayConfigValidation,
    XrayValidationOutcome,
)


class IXrayConfigGateway(Protocol):
    async def validate(
        self,
        *,
        node_id: int,
        address: str,
        port: int,
        instance_id: str,
        source: bytes,
    ) -> XrayValidationOutcome: ...


class IXrayConfigValidation(Protocol):
    async def validate(
        self,
        node_id: int,
        instance_id: str,
        candidate: XrayConfigCandidate,
    ) -> XrayConfigValidation: ...
