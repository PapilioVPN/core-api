"""Dispatch committed start operations from JetStream."""

from dishka import FromDishka
from faststream import AckPolicy
from papilio_tasks.apps.events.routers.nats import NatsRouter

from ...app.pipelines.start import XrayStartPipeline
from ...domain.events.start import XrayStartRequested
from ...infra.broker.config import BrokerConfig
from ...infra.broker.publishers import start_requested

router = NatsRouter()


@router.subscriber(
    publisher=start_requested,
    durable=BrokerConfig.start_durable,
    pull_sub=True,
    max_workers=4,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def dispatch_start(
    event: XrayStartRequested, *, pipeline: FromDishka[XrayStartPipeline]
) -> None:
    """Run the committed operation behind an identity-only delivery."""
    await pipeline.run(event.operation_id)
