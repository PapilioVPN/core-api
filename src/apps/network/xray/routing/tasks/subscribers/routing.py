"""Dispatch committed Xray routing operation identities."""

from dishka import FromDishka
from faststream import AckPolicy
from papilio_tasks.apps.events.routers.nats import NatsRouter

from ...app.pipelines.routing import XrayRoutingPipeline
from ...domain.events.control import RoutingRequested
from ...infra.broker.config import BrokerConfig
from ...infra.broker.publishers import routing_requested

router = NatsRouter()


@router.subscriber(
    publisher=routing_requested,
    durable=BrokerConfig.durable,
    pull_sub=True,
    max_workers=4,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def dispatch_routing(
    event: RoutingRequested, *, pipeline: FromDishka[XrayRoutingPipeline]
) -> None:
    """Run the committed routing operation once."""
    await pipeline.run(event.operation_id)
