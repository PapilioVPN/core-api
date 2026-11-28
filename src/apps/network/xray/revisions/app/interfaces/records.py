"""Persistence, encryption and application contracts for Xray revisions."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import (
    XrayRevisionCreate,
    XrayRevisionList,
    XrayRevisionSelectionInput,
)
from ...domain.models.records import XrayRevisionModel
from ...domain.results.inbounds import XrayRevisionInbounds
from ...domain.results.records import (
    XrayRevision,
    XrayRevisionChoice,
    XrayRevisionSave,
    XrayRevisionSelection,
    XrayRevisionSource,
    XraySealedSource,
    XraySourceFailure,
)


class IXraySourceDigest(Protocol):
    async def digest(self, source: bytes) -> str: ...


class IXrayRevisionSourceCodec(Protocol):
    async def seal(
        self, source: bytes
    ) -> XraySealedSource | XraySourceFailure: ...

    async def open(
        self, ciphertext: str
    ) -> XrayRevisionSource | XraySourceFailure: ...


class IXrayRevisionRepository(Protocol):
    async def insert(self, data: XrayRevisionModel) -> int | None: ...

    async def get_by_id(self, id: int) -> XrayRevisionModel | None: ...


class IXrayRevisionReader(Protocol):
    async def for_id(self, id: int) -> XrayRevision | None: ...

    async def for_digest(self, digest: str) -> XrayRevision | None: ...

    async def list(
        self, *, limit: int, offset: int
    ) -> PagedType[XrayRevision]: ...

    async def select_choices(
        self, *, before_id: int | None, limit: int
    ) -> tuple[XrayRevisionChoice, ...]: ...


class IXrayRevisionSelectionQuery(Protocol):
    async def get(
        self, data: XrayRevisionSelectionInput
    ) -> XrayRevisionSelection: ...


class IXrayRevisionInboundsQuery(Protocol):
    async def get(self, id: int) -> XrayRevisionInbounds: ...


class IXrayRevisionService(Protocol):
    async def save(
        self, data: XrayRevisionCreate
    ) -> XrayRevisionSave | XraySourceFailure: ...

    async def get_by_id(self, id: int) -> XrayRevision: ...

    async def list(
        self, data: XrayRevisionList
    ) -> PagedType[XrayRevision]: ...

    async def get_source(
        self, id: int
    ) -> XrayRevisionSource | XraySourceFailure: ...
