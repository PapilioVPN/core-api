"""Read individual or selected sets of node management endpoints."""

from typing import Protocol

from ...domain.results.records import NodeEndpoint


class INodeEndpointQuery(Protocol):
    async def get_endpoint(self, id: int) -> NodeEndpoint: ...

    async def get_endpoints(
        self, ids: tuple[int, ...]
    ) -> dict[int, NodeEndpoint]: ...


class INodeEndpointReader(Protocol):
    async def select_endpoint(self, id: int) -> NodeEndpoint | None: ...

    async def select_endpoints(
        self, ids: tuple[int, ...]
    ) -> dict[int, NodeEndpoint]: ...
