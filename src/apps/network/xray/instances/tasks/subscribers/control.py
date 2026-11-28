"""Receive durable Xray lifecycle requests from JetStream."""

from dishka import FromDishka
from faststream import AckPolicy
from papilio_tasks.apps.events.routers.nats import NatsRouter

from ...app.pipelines.control import XrayControlPipeline
from ...domain.events.control import XrayControlRequested
from ...infra.broker.config import BrokerConfig
from ...infra.broker.publishers import control_requested

router = NatsRouter()


@router.subscriber(
    publisher=control_requested,
    durable=BrokerConfig.control_durable,
    pull_sub=True,
    max_workers=4,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def dispatch_control(
    event: XrayControlRequested,
    *,
    pipeline: FromDishka[XrayControlPipeline],
) -> None:
    """Run the typed Stop or Restart recorded under this identity."""
    await pipeline.run(event.operation_id)
