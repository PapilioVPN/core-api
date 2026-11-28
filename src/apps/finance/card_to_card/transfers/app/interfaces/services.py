"""Record incoming transfers and read them from the Finance panel."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import TransferList
from ...domain.models.records import TransferModel


class ITransferService(Protocol):
    async def create(self, data: TransferModel) -> TransferModel: ...

    async def list(self, data: TransferList) -> PagedType[TransferModel]: ...

    async def get_by_id(self, id: int) -> TransferModel: ...
