"""Customer search contract for the administrator panel."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.search import ProfileSearch
from ...domain.models.records import CustomerModel


class IProfileSearch(Protocol):
    async def search(
        self, data: ProfileSearch
    ) -> PagedType[CustomerModel]: ...
