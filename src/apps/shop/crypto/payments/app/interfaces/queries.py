"""Crypto payment reads for the administrator panel."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.search import PaymentSearch
from ...domain.models.records import CryptoPaymentModel


class ICryptoPaymentSearchQuery(Protocol):
    async def search(
        self, data: PaymentSearch
    ) -> PagedType[CryptoPaymentModel]: ...
