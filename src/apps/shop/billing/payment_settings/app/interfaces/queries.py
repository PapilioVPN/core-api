"""The cache-safe payment settings view consumed by the panel."""

from typing import Protocol

from ...domain.results.records import PaymentSettingsView


class IPaymentSettingsQuery(Protocol):
    async def get(self) -> PaymentSettingsView: ...
