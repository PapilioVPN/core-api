"""Issuer-checked payment card writes for the administrator panel."""

from typing import Protocol

from ...domain.dtos.records import CardCreate, CardUpdate
from ...domain.models.records import PaymentCardModel


class ICardCommand(Protocol):
    async def create(self, data: CardCreate) -> PaymentCardModel: ...

    async def update(self, id: int, data: CardUpdate) -> PaymentCardModel: ...
