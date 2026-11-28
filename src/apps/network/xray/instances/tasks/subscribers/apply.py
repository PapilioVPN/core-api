"""Dispatch committed revision applications from JetStream."""

from dishka import FromDishka
from faststream import AckPolicy
from papilio_tasks.apps.events.routers.nats import NatsRouter

from ...app.pipelines.start import XrayStartPipeline
from ...domain.events.apply import XrayApplyRequested
from ...infra.broker.config import BrokerConfig
from ...infra.broker.publishers import apply_requested

router = NatsRouter()


@router.subscriber(
    publisher=apply_requested,
    durable=BrokerConfig.apply_durable,
    pull_sub=True,
    max_workers=4,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def dispatch_apply(
    event: XrayApplyRequested, *, pipeline: FromDishka[XrayStartPipeline]
) -> None:
    """Dispatch the same native Start RPC with the stored revision source."""
    await pipeline.run(event.operation_id)
