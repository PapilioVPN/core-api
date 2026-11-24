"""Bind the optional receipt OCR consumer to the existing publication."""

from dishka import FromDishka
from faststream import AckPolicy, StreamMessage
from papilio_tasks.apps.events.routers.nats import NatsRouter

from src.apps.shop.billing.receipts.domain.events.records import ReceiptCreated
from src.apps.shop.billing.receipts.infra.broker.publishers import (
    receipt_created,
)

from ...app.pipelines.receipts import OCRPipeline


async def process(
    event: ReceiptCreated,
    *,
    pipeline: FromDishka[OCRPipeline],
    message: FromDishka[StreamMessage],
) -> None:
    """Process a committed receipt using its durable event identity."""
    await pipeline.process(
        event.receipt_id, event_id=message.headers["event_id"]
    )


def create_router() -> NatsRouter:
    """Include receipt recognition when its endpoint has been configured."""
    router = NatsRouter()
    router.subscriber(
        publisher=receipt_created,
        durable="papiliovpn_receipt_ocr",
        pull_sub=True,
        ack_policy=AckPolicy.NACK_ON_ERROR,
    )(process)
    return router
