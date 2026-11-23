"""Storefront reads for services."""

from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.services.domain.dtos.public import PublicServiceSearch
from src.apps.shop.services.domain.results.public import PublicService


class IPublicServiceQuery(Protocol):
    async def search(
        self, data: PublicServiceSearch
    ) -> PagedType[PublicService]: ...
