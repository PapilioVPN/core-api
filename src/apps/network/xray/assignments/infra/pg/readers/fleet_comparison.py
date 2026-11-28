"""Read digest metadata for exactly the selected Xray targets."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import select, tuple_
from sqlmodel import col

from src.apps.network.xray.instances.domain.dtos.identity import (
    XrayExecutionKey,
)
from src.apps.network.xray.revisions.infra.pg.tables import XrayRevisionTable

from ....domain.results.records import XrayDesiredRevision
from ..tables import XrayDesiredRevisionTable


class XrayAssignmentReader(PGReader):
    async def select_desired(
        self, keys: tuple[XrayExecutionKey, ...]
    ) -> dict[XrayExecutionKey, XrayDesiredRevision]:
        """Read desired metadata without selecting or decrypting config bytes.

        Args:
            keys: Nonempty bounded set of exact registry and instance pairs.

        Returns:
            Metadata keyed by assigned pair. Unassigned pairs are absent.
        """
        assignment = XrayDesiredRevisionTable
        revision = XrayRevisionTable
        stmt = (
            select(
                col(assignment.node_id),
                col(assignment.instance_id),
                col(assignment.revision_id),
                col(revision.config_sha256),
                col(assignment.updated_at),
            )
            .join(revision, col(revision.id) == col(assignment.revision_id))
            .where(
                tuple_(
                    col(assignment.node_id), col(assignment.instance_id)
                ).in_(keys)
            )
        )
        result = await self.uow.execute(stmt)
        rows = result.tuples()
        return {
            (node, instance): XrayDesiredRevision(revision_id, digest, at)
            for node, instance, revision_id, digest, at in rows
        }
