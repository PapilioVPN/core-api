"""Registration and reads for wallet top-up requests."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import DepositCreate, DepositSearch
from ...domain.models.records import WalletDepositModel


class IWalletDepositService(Protocol):
    async def create(
        self, customer_id: int, data: DepositCreate
    ) -> WalletDepositModel: ...

    async def get_by_id(
        self, customer_id: int, id: int
    ) -> WalletDepositModel: ...

    async def search(
        self, customer_id: int, data: DepositSearch
    ) -> PagedType[WalletDepositModel]: ...
