"""Project only the facts needed to select a management connection."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import Select, select
from sqlmodel import col

from ....domain.results.records import NodeEndpoint
from ..tables import NodeTable


class NodeEndpointReader(PGReader):
    async def select_endpoint(self, id: int) -> NodeEndpoint | None:
        """Read one endpoint by its registry ID."""
        stmt = self._projection().where(col(NodeTable.id) == id)
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return NodeEndpoint(*row) if row is not None else None

    async def select_endpoints(
        self, ids: tuple[int, ...]
    ) -> dict[int, NodeEndpoint]:
        """Materialize selected endpoints in one bounded query."""
        stmt = self._projection().where(col(NodeTable.id).in_(ids))
        result = await self.uow.execute(stmt)
        return {
            id: NodeEndpoint(id, address, port, enabled)
            for id, address, port, enabled in result.tuples()
        }

    @staticmethod
    def _projection() -> Select[tuple[int, str, int, bool]]:
        return select(
            col(NodeTable.id),
            col(NodeTable.address),
            col(NodeTable.port),
            col(NodeTable.is_enabled),
        )
