"""Issuer-checked payment card writes for the administrator panel."""

from typing import Protocol

from ...domain.dtos.records import CardCreate, CardUpdate
from ...domain.models.records import PaymentCardModel


class ICardCreateCommand(Protocol):
    async def create(self, data: CardCreate) -> PaymentCardModel: ...


class ICardUpdateCommand(Protocol):
    async def update(self, id: int, data: CardUpdate) -> PaymentCardModel: ...
