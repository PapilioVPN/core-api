"""Typed contracts for validating a proposal against an Xray instance."""

from typing import Protocol

from src.apps.network.xray.revisions.domain.dtos.source import (
    XrayConfigCandidate,
)
from src.apps.network.xray.revisions.domain.results.records import (
    XraySourceFailure,
)

from ...domain.results.dry_run import (
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

    async def validate_revision(
        self, node_id: int, instance_id: str, revision_id: int
    ) -> XrayConfigValidation | XraySourceFailure: ...
