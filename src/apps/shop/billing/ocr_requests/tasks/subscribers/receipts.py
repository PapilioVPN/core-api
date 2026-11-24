"""Bind the optional receipt OCR consumer to the existing publication."""

from dishka import FromDishka
from faststream import AckPolicy, StreamMessage
from papilio_tasks.apps.events.routers.nats import NatsRouter

from src.apps.shop.billing.receipts.domain.events.records import ReceiptCreated
from src.apps.shop.billing.receipts.infra.broker.publishers import (
    receipt_created,
)

from ...app.interfaces.processing import IOCRPipeline
from ...infra.broker.config import BrokerConfig

router = NatsRouter()


@router.subscriber(
    publisher=receipt_created,
    durable=BrokerConfig.receipt_durable,
    pull_sub=True,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
async def process(
    event: ReceiptCreated,
    *,
    pipeline: FromDishka[IOCRPipeline],
    message: FromDishka[StreamMessage],
) -> None:
    """Process a committed receipt using its durable event identity."""
    await pipeline.process(
        event.receipt_id, event_id=message.headers["event_id"]
    )
