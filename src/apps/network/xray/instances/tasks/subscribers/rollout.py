"""Deliver the current rollout operation over durable JetStream."""

from dishka import FromDishka
from faststream import AckPolicy
from faststream.exceptions import NackMessage
from papilio_tasks.apps.events.routers.nats import NatsRouter

from ...app.pipelines.rollout import RestartRolloutPipeline
from ...domain.events.rollout import XrayRestartRolloutRequested
from ...infra.broker.config import BrokerConfig
from ...infra.broker.publishers import rollout_requested

router = NatsRouter()


@router.subscriber(
    publisher=rollout_requested,
    durable=BrokerConfig.rollout_durable,
    pull_sub=True,
    max_workers=2,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def run_rollout(
    event: XrayRestartRolloutRequested,
    *,
    pipeline: FromDishka[RestartRolloutPipeline],
) -> None:
    """Delay duplicate running deliveries until their dispatch deadline."""
    retry_after = await pipeline.run(event.rollout_id, event.operation_id)
    if retry_after is not None:
        raise NackMessage(delay=retry_after)
