"""Dispatch committed Xray traffic reset operation identities."""

from dishka import FromDishka
from faststream import AckPolicy
from papilio_tasks.apps.events.routers.nats import NatsRouter

from ...app.pipelines.reset import XrayResetPipeline
from ...domain.events.reset import TrafficResetRequested
from ...infra.broker.config import BrokerConfig
from ...infra.broker.publishers import traffic_reset_requested

router = NatsRouter()


@router.subscriber(
    publisher=traffic_reset_requested,
    durable=BrokerConfig.durable,
    pull_sub=True,
    max_workers=4,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def dispatch_traffic_reset(
    event: TrafficResetRequested, *, pipeline: FromDishka[XrayResetPipeline]
) -> None:
    """Run the committed traffic reset operation once."""
    await pipeline.run(event.operation_id)
