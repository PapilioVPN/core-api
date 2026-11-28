"""Contracts for trusted internal IPG link creation."""

from typing import Protocol

from ...domain.dtos.records import PaymentCreate
from ...domain.results.link import LinkRequest, PaymentLink, ProviderLink
from ...domain.results.verify import Verification


class ICreatePaymentCommand(Protocol):
    async def create(self, data: PaymentCreate) -> PaymentLink: ...


class ILinkExecution(Protocol):
    async def prepare(self, data: PaymentCreate) -> LinkRequest: ...

    async def finish(self, id: int, link: ProviderLink) -> PaymentLink: ...


class IPGGateway(Protocol):
    async def create(self, request: LinkRequest) -> ProviderLink: ...

    async def verify(self, request: Verification) -> str | None: ...


class IZarinPalClient(IPGGateway, Protocol):
    pass


class IZibalClient(IPGGateway, Protocol):
    pass
