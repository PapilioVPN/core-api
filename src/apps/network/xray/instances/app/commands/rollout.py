"""Register an immutable ordered restart selection and its first operation."""

from uuid import UUID

from papilio.errors.exceptions import ConflictException, NotFoundException
from papilio.infra.db.tools.decorators import transactional
from papilio.utils.dates import utc_now

from src.apps.network.nodes.app.interfaces.endpoints import INodeEndpointQuery
from src.apps.network.xray.revisions.app.interfaces.records import (
    IXrayRevisionService,
)

from ...domain.dtos.rollout import RestartRolloutInput
from ...domain.models.rollout import (
    XrayRestartRolloutModel,
    XrayRestartRolloutTargetModel,
)
from ...domain.results.rollout import RestartRolloutSnapshot
from ..interfaces.rollout import (
    IRestartRolloutReader,
    IRestartRolloutRepository,
)
from ..services.rollout_schedule import RestartRolloutSchedule


class RestartRolloutCommand:
    def __init__(
        self,
        revisions: IXrayRevisionService,
        nodes: INodeEndpointQuery,
        repository: IRestartRolloutRepository,
        reader: IRestartRolloutReader,
        schedule: RestartRolloutSchedule,
    ) -> None:
        self.revisions = revisions
        self.nodes = nodes
        self.repository = repository
        self.reader = reader
        self.schedule = schedule

    @transactional
    async def submit(
        self,
        revision_id: int,
        request_key: UUID,
        data: RestartRolloutInput,
    ) -> RestartRolloutSnapshot:
        """Commit one stable plan or replay its current durable snapshot."""
        plan = await self.repository.find_request(request_key)
        if plan is None:
            revision = await self.revisions.get_by_id(revision_id)
            plan = await self.repository.insert(
                XrayRestartRolloutModel(
                    request_key=request_key,
                    revision_id=revision.id,
                    config_sha256=revision.config_sha256,
                )
            )
            if plan is None:
                plan = await self.repository.find_request(request_key)
            else:
                await self._capture(plan, data)
        if plan is None:
            raise RuntimeError(
                "Restart rollout insert lost its request identity"
            )
        snapshot = await self.reader.read(plan.revision_id, plan.id)
        if snapshot is None:
            raise RuntimeError("A persisted restart rollout has no targets")
        selected = [(row.node_id, row.instance_id) for row in data.targets]
        stored = [
            (row.target.node_id, row.target.instance_id)
            for row in snapshot.steps
        ]
        if plan.revision_id != revision_id or selected != stored:
            raise ConflictException(
                message="The rollout key identifies a different selection.",
                message_code="xray_rollout_key_conflict",
                unique_dict={},
            )
        return snapshot

    async def _capture(
        self, plan: XrayRestartRolloutModel, data: RestartRolloutInput
    ) -> None:
        endpoints = await self.nodes.get_endpoints(
            tuple(dict.fromkeys(row.node_id for row in data.targets))
        )
        targets = []
        for position, row in enumerate(data.targets, start=1):
            endpoint = endpoints.get(row.node_id)
            if endpoint is None:
                raise NotFoundException(
                    message="A selected Node is not registered.",
                    message_code="xray_rollout_node_not_found",
                    entity="Node",
                    identifier="id",
                    identifier_value=row.node_id,
                )
            if not endpoint.is_enabled:
                raise ConflictException(
                    message="A selected Node is disabled.",
                    message_code="xray_rollout_node_disabled",
                    unique_dict={"node_id": row.node_id},
                )
            targets.append(
                XrayRestartRolloutTargetModel(
                    rollout_id=plan.id,
                    position=position,
                    node_id=row.node_id,
                    instance_id=row.instance_id,
                    address=endpoint.address,
                    port=endpoint.port,
                )
            )
        await self.repository.add_targets(tuple(targets))
        first = await self.repository.target(plan.id, 1)
        if first is None:
            raise RuntimeError("The initial restart target was not persisted")
        await self.schedule.enqueue(plan, first, utc_now())
