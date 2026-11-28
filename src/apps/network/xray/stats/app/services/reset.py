"""Durably register the exact reset and publish only its identity."""

from uuid import UUID

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.network.nodes.app.interfaces.services import INodeService

from ...domain.events.reset import TrafficResetRequested
from ...domain.models.reset import XrayTrafficResetModel
from ...domain.results.reset import ResetSelection
from ...infra.broker.publishers import traffic_reset_requested
from ..interfaces.reset import IXrayResetRepository


class XrayTrafficResets(IDChecks[XrayTrafficResetModel]):
    entity = "Xray traffic reset"

    def __init__(
        self,
        nodes: INodeService,
        repo: IXrayResetRepository,
        outbox: OutboxWriter,
    ) -> None:
        self.nodes = nodes
        self.repo = repo
        self.outbox = outbox

    @transactional
    async def submit(
        self,
        node_id: int,
        instance_id: str,
        key: UUID,
        selection: ResetSelection,
    ) -> XrayTrafficResetModel:
        """Return the committed operation or its exact replay."""
        operation = await self.repo.find_request(node_id, instance_id, key)
        if operation is None:
            node = await self.nodes.get_by_id(node_id)
            if not node.is_enabled:
                raise ConflictException(
                    message="The Node is disabled.",
                    message_code="xray_reset_node_disabled",
                    unique_dict={},
                )
            await self.repo.expire(node_id, instance_id, utc_now())
            operation = await self.repo.insert(
                XrayTrafficResetModel(
                    node_id=node_id,
                    instance_id=instance_id,
                    address=node.address,
                    port=node.port,
                    request_key=key,
                    scope=selection.scope,
                    kind=selection.kind,
                    name=selection.name,
                    direction=selection.direction,
                    max_counters=selection.max_counters,
                )
            )
            if operation is not None:
                await self.outbox.append(
                    traffic_reset_requested,
                    TrafficResetRequested(operation_id=operation.id),
                )
            else:
                operation = await self.repo.find_request(
                    node_id, instance_id, key
                )
                if operation is None:
                    raise ConflictException(
                        message="A traffic reset is active.",
                        message_code="xray_reset_active",
                        unique_dict={},
                    )
        if operation.selection() != selection:
            raise ConflictException(
                message="The reset key identifies a different request.",
                message_code="xray_reset_key_conflict",
                unique_dict={},
            )
        return operation.observed_at(utc_now())

    @transactional
    async def get(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayTrafficResetModel:
        """Read the result under its original Node and instance."""
        operation = await self.repo.find_operation(node_id, instance_id, id)
        return self._check_for_id_existence(id, operation).observed_at(
            utc_now()
        )
