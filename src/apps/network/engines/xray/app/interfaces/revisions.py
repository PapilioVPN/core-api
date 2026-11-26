"""Persistence, encryption and application contracts for Xray revisions."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.revisions import XrayRevisionCreate, XrayRevisionList
from ...domain.models.revisions import XrayRevisionModel
from ...domain.results.revisions import (
    XrayRevision,
    XrayRevisionSave,
    XrayRevisionSource,
)


class IXrayRevisionCipher(Protocol):
    def seal(self, source: bytes) -> str: ...

    def open(self, ciphertext: str) -> bytes: ...


class IXrayRevisionRepository(Protocol):
    async def insert(self, data: XrayRevisionModel) -> int | None: ...

    async def get_by_id(self, id: int) -> XrayRevisionModel | None: ...


class IXrayRevisionReader(Protocol):
    async def for_id(self, id: int) -> XrayRevision | None: ...

    async def for_digest(self, digest: str) -> XrayRevision | None: ...

    async def list(
        self, *, limit: int, offset: int
    ) -> PagedType[XrayRevision]: ...


class IXrayRevisionService(Protocol):
    async def save(self, data: XrayRevisionCreate) -> XrayRevisionSave: ...

    async def get_by_id(self, id: int) -> XrayRevision: ...

    async def list(
        self, data: XrayRevisionList
    ) -> PagedType[XrayRevision]: ...

    async def get_source(self, id: int) -> XrayRevisionSource: ...
