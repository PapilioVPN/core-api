"""Panel management and webhook verification for card API keys."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import APIKeyCreate, APIKeyList
from ...domain.models.records import APIKeyModel
from ...domain.results.issued import IssuedAPIKey


class IAPIKeyService(Protocol):
    async def create(self, data: APIKeyCreate) -> IssuedAPIKey: ...

    async def list(self, data: APIKeyList) -> PagedType[APIKeyModel]: ...

    async def get_by_id(self, id: int) -> APIKeyModel: ...

    async def revoke(self, id: int) -> APIKeyModel: ...

    async def verify(self, key: str) -> int | None: ...
