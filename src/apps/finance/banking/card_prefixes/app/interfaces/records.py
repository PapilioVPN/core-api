"""Owning application contracts for this capability."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.finance.banking.card_prefixes.domain.dtos.records import (
    CardPrefixCreate,
    CardPrefixList,
    CardPrefixUpdate,
)
from src.apps.finance.banking.card_prefixes.domain.models.records import (
    CardPrefixModel,
)


class ICardPrefixCreateCommand(Protocol):
    async def create(self, data: CardPrefixCreate) -> CardPrefixModel: ...


class ICardPrefixUpdateCommand(Protocol):
    async def update(
        self, id: int, data: CardPrefixUpdate
    ) -> CardPrefixModel: ...


class ICardPrefixService(Protocol):
    async def create(self, data: CardPrefixCreate) -> CardPrefixModel: ...

    async def get_by_id(self, id: int) -> CardPrefixModel: ...

    async def find_by_id(self, id: int) -> CardPrefixModel | None: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CardPrefixModel]: ...

    async def get_by_prefix(self, prefix: str) -> CardPrefixModel: ...

    async def find_by_prefix(self, prefix: str) -> CardPrefixModel | None: ...

    async def get_by_prefixes(
        self, prefixes: Sequence[str]
    ) -> Sequence[CardPrefixModel]: ...

    async def list(
        self, query: CardPrefixList
    ) -> PagedType[CardPrefixModel]: ...

    async def update(
        self, id: int, data: CardPrefixUpdate
    ) -> CardPrefixModel: ...

    async def remove(self, id: int) -> CardPrefixModel: ...
