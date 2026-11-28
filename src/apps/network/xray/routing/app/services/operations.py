"""Admit typed routing changes and retain their delivery evidence."""

from uuid import UUID

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.network.nodes.app.interfaces.services import INodeService

from ...domain.dtos.mutations import RoutingIntent
from ...domain.enums.operation import RoutingAction, RoutingPayloadFailure
from ...domain.events.control import RoutingRequested
from ...domain.models.operation import XrayRoutingOperationModel
from ...domain.results.operation import RoutingPayload
from ...infra.broker.publishers import routing_requested
from ..interfaces.operations import (
    IRoutingPayloadCodec,
    IXrayRoutingOperationRepository,
)


class XrayRoutingOperations(IDChecks[XrayRoutingOperationModel]):
    entity = "Xray routing operation"

    def __init__(
        self,
        nodes: INodeService,
        repo: IXrayRoutingOperationRepository,
        codec: IRoutingPayloadCodec,
        outbox: OutboxWriter,
    ) -> None:
        self.nodes = nodes
        self.repo = repo
        self.codec = codec
        self.outbox = outbox

    async def submit(
        self, node_id: int, instance_id: str, key: UUID, intent: RoutingIntent
    ) -> XrayRoutingOperationModel | RoutingPayloadFailure:
        """Register an operator mutation and publish only its durable identity.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native Xray instance identity.
            key: Idempotency key scoped to the instance.
            intent: Typed operator-selected routing action.

        Returns:
            Committed or replayed operation, or a protection failure.

        Raises:
            NotFoundException: The Node is absent from the registry.
            ConflictException: The target is disabled, busy or the key differs.
        """
        payload = await self.codec.seal(intent)
        if isinstance(payload, RoutingPayloadFailure):
            operation = payload
        else:
            operation = await self._admit(
                node_id, instance_id, key, intent.action, payload
            )
        return operation

    @transactional
    async def _admit(
        self,
        node_id: int,
        instance_id: str,
        key: UUID,
        action: RoutingAction,
        payload: RoutingPayload,
    ) -> XrayRoutingOperationModel:
        existing = await self.repo.find_request(node_id, instance_id, key)
        if existing is None:
            node = await self.nodes.get_by_id(node_id)
            if not node.is_enabled:
                raise ConflictException(
                    message="The Node is disabled.",
                    message_code="xray_routing_node_disabled",
                    unique_dict={},
                )
            await self.repo.expire(node_id, instance_id, utc_now())
            existing = await self.repo.insert(
                XrayRoutingOperationModel(
                    node_id=node_id,
                    instance_id=instance_id,
                    address=node.address,
                    port=node.port,
                    request_key=key,
                    action=action,
                    payload_digest=payload.digest,
                    ciphertext=payload.ciphertext,
                )
            )
            if existing is not None:
                await self.outbox.append(
                    routing_requested,
                    RoutingRequested(operation_id=existing.id),
                )
            else:
                existing = await self.repo.find_request(
                    node_id, instance_id, key
                )
                if existing is None:
                    raise ConflictException(
                        message="A routing operation is active.",
                        message_code="xray_routing_active",
                        unique_dict={},
                    )
        if (
            existing.payload_digest != payload.digest
            or existing.action != action
        ):
            raise ConflictException(
                message="The routing key identifies a different request.",
                message_code="xray_routing_key_conflict",
                unique_dict={},
            )
        return existing.observed_at(utc_now())

    @transactional
    async def get(
        self, node_id: int, instance_id: str, id: int
    ) -> XrayRoutingOperationModel:
        """Read a tracking record without re-running its native mutation.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native Xray instance identity.
            id: Persisted operation identity owned by that instance.

        Returns:
            The operation and its current delivery evidence.

        Raises:
            NotFoundException: The operation is absent under this instance.
        """
        operation = self._check_for_id_existence(
            id, await self.repo.find_operation(node_id, instance_id, id)
        )
        return operation.observed_at(utc_now())
