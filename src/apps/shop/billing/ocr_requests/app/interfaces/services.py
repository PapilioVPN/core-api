"""Record operations owned by receipt OCR."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import OCRRequestList
from ...domain.models.records import OCRRequestModel


class IOCRRequestService(Protocol):
    async def create(
        self, data: OCRRequestModel
    ) -> OCRRequestModel | None: ...

    async def exists_by_event(self, event_id: str) -> bool: ...

    async def get_by_id(self, id: int) -> OCRRequestModel: ...

    async def find_by_event(self, event_id: str) -> OCRRequestModel | None: ...

    async def list(
        self, query: OCRRequestList
    ) -> PagedType[OCRRequestModel]: ...
