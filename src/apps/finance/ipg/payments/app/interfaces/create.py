"""Contracts for trusted internal IPG link creation."""

from typing import Protocol

from ...domain.dtos.records import PaymentCreate
from ...domain.results.link import LinkRequest, PaymentLink, ProviderLink


class ICreatePaymentCommand(Protocol):
    async def create(self, data: PaymentCreate) -> PaymentLink: ...


class ILinkExecution(Protocol):
    async def prepare(self, data: PaymentCreate) -> LinkRequest: ...

    async def finish(self, id: int, link: ProviderLink) -> PaymentLink: ...


class IPaymentClient(Protocol):
    async def create(self, request: LinkRequest) -> ProviderLink: ...


class IZarinPalClient(IPaymentClient, Protocol):
    pass


class IZibalClient(IPaymentClient, Protocol):
    pass
