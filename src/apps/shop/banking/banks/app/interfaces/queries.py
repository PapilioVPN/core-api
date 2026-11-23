"""Bank reference operations for the panel and payment card commands."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import BankList
from ...domain.models.records import BankModel
from ...domain.results.prefix import BankMatch


class IBankQuery(Protocol):
    async def get_by_id(self, id: int) -> BankModel: ...

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[BankModel]: ...

    async def find_by_prefix(self, prefix: str) -> BankMatch | None: ...

    async def get_by_prefix(self, prefix: str) -> BankMatch: ...

    async def list(self, query: BankList) -> PagedType[BankModel]: ...
