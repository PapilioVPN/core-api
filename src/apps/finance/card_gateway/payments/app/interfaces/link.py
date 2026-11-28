"""Contracts for hosted link creation and its independent phases."""

from typing import Protocol

from pydantic import HttpUrl

from ...domain.results.link import LinkPreparation, LinkRequest, LinkResult


class ICreateLinkCommand(Protocol):
    async def create(self, id: int, return_url: HttpUrl) -> LinkResult: ...


class ILinkExecution(Protocol):
    async def prepare(self, id: int) -> LinkPreparation: ...

    async def finish(self, id: int, result: LinkResult) -> LinkResult: ...


class IVarizaClient(Protocol):
    async def create(
        self, request: LinkRequest, return_url: HttpUrl
    ) -> LinkResult: ...
