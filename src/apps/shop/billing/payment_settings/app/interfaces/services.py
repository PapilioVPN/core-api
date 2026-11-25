"""Operations owned by the payment settings module."""

from typing import Protocol

from ...domain.dtos.records import PaymentSettingsWrite
from ...domain.models.records import PaymentSettingsModel


class IPaymentSettingsService(Protocol):
    async def get(self) -> PaymentSettingsModel: ...

    async def save(
        self, data: PaymentSettingsWrite
    ) -> PaymentSettingsModel: ...

    async def issue_key(self) -> str: ...

    async def revoke_key(self) -> None: ...
