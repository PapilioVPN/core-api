"""Service operations for the panel and other shop capabilities."""

from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.services.domain.dtos.records import (
    ServiceCreate,
    ServiceList,
    ServiceUpdate,
)
from src.apps.shop.services.domain.models.records import ServiceModel


class IServices(Protocol):
    async def create(self, data: ServiceCreate) -> ServiceModel: ...

    async def get_by_id(self, id: int) -> ServiceModel: ...

    async def list(self, query: ServiceList) -> PagedType[ServiceModel]: ...

    async def update(self, id: int, data: ServiceUpdate) -> ServiceModel: ...
