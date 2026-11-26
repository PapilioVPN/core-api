"""Durably admit one configured start and publish its identity."""

from uuid import UUID

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter

from src.apps.network.nodes.app.interfaces.services import INodeService

from ...domain.enums.start import XrayStartState
from ...domain.events.start import XrayStartRequested
from ...domain.models.start import XrayStartModel
from ...infra.broker.publishers import start_requested
from ..interfaces.start import IXrayStartRepository


class XrayStartCommand:
    def __init__(
        self,
        repo: IXrayStartRepository,
        nodes: INodeService,
        outbox: OutboxWriter,
    ) -> None:
        self.repo = repo
        self.nodes = nodes
        self.outbox = outbox

    @transactional
    async def submit(
        self, node_id: int, instance_id: str, request_key: UUID
    ) -> XrayStartModel:
        """Register a request or recover the result of the same request key.

        Args:
            node_id: Stable node registry identity.
            instance_id: Native Xray instance identity.
            request_key: Operator request identity within this target.

        Returns:
            The operation with a tracking identity upon transaction commit.

        Raises:
            NotFoundException: The requested Node does not exist.
            ConflictException: The Node is disabled or the instance is busy.
        """
        record = await self.repo.find_request(
            node_id, instance_id, request_key
        )
        if record is None:
            node = await self.nodes.get_by_id(node_id)
            if not node.is_enabled:
                raise ConflictException(
                    message="The Node is disabled.",
                    message_code="xray_start_node_disabled",
                    unique_dict={},
                )
            await self.repo.expire(node_id, instance_id, utc_now())
            record = await self.repo.insert(
                XrayStartModel(
                    node_id=node_id,
                    instance_id=instance_id,
                    request_key=request_key,
                    address=node.address,
                    port=node.port,
                    state=XrayStartState.QUEUED,
                )
            )
            if record is None:
                record = await self.repo.find_request(
                    node_id, instance_id, request_key
                )
                if record is None:
                    raise ConflictException(
                        message="A start is already active for this instance.",
                        message_code="xray_start_active",
                        unique_dict={},
                    )
            else:
                await self.outbox.append(
                    start_requested, XrayStartRequested(operation_id=record.id)
                )
        return record.observed_at(utc_now())
