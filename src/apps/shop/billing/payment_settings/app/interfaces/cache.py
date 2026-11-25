"""The singleton settings cache used by the panel query and writes."""

from typing import Protocol

from ...domain.results.records import PaymentSettingsView


class IPaymentSettingsCache(Protocol):
    async def find(self) -> PaymentSettingsView | None: ...

    async def store(self, view: PaymentSettingsView, ttl: int) -> None: ...

    async def forget(self) -> None: ...


class IPaymentSettingsCacheOwner(Protocol):
    @property
    def cache(self) -> IPaymentSettingsCache: ...
