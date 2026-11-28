"""Persistence, encryption and application contracts for Xray revisions."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import (
    XrayRevisionBulkRemoveInput,
    XrayRevisionCreate,
    XrayRevisionList,
    XrayRevisionOrderInput,
    XrayRevisionSelectionInput,
)
from ...domain.enums.removal import XrayRevisionRemovalStatus
from ...domain.models.records import XrayRevisionModel
from ...domain.results.inbounds import XrayRevisionInbounds
from ...domain.results.records import (
    XrayRevision,
    XrayRevisionChoice,
    XrayRevisionSave,
    XrayRevisionSelection,
    XrayRevisionSource,
    XraySealedSource,
)
from ...domain.results.removal import XrayRevisionRemoval


class IXraySourceDigest(Protocol):
    async def digest(self, source: bytes) -> str: ...


class IXrayRevisionSourceCodec(Protocol):
    async def seal(self, source: bytes) -> XraySealedSource | None: ...

    async def open(self, ciphertext: str) -> XrayRevisionSource | None: ...


class IXrayRevisionRepository(Protocol):
    async def insert(self, data: XrayRevisionModel) -> int | None: ...

    async def get_by_id(self, id: int) -> XrayRevisionModel | None: ...

    async def lock_sort_positions(
        self, ids: tuple[int, ...]
    ) -> dict[int, int]: ...

    async def set_sort_positions(self, positions: dict[int, int]) -> None: ...

    async def remove_unreferenced_by_id(
        self, id: int
    ) -> XrayRevisionRemovalStatus: ...

    async def remove_unreferenced_by_ids(
        self, ids: tuple[int, ...]
    ) -> tuple[XrayRevisionRemoval, ...]: ...


class IXrayRevisionReader(Protocol):
    async def for_id(self, id: int) -> XrayRevision | None: ...

    async def lock_by_digest(self, digest: str) -> XrayRevision | None: ...

    async def lock_for_reference(self, id: int) -> XrayRevision | None: ...

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
    ) -> XrayRevisionSave | None: ...

    async def get_by_id(self, id: int) -> XrayRevision: ...

    async def lock_for_reference(self, id: int) -> XrayRevision: ...

    async def remove(self, id: int) -> None: ...

    async def remove_many(
        self, data: XrayRevisionBulkRemoveInput
    ) -> tuple[XrayRevisionRemoval, ...]: ...

    async def reorder(self, data: XrayRevisionOrderInput) -> None: ...

    async def list(
        self, data: XrayRevisionList
    ) -> PagedType[XrayRevision]: ...

    async def get_source(self, id: int) -> XrayRevisionSource | None: ...
