"""Exercise receipt OCR with a controlled PaddleOCR response."""

import json
from base64 import b64decode
from pathlib import Path

import pytest
from anyio.streams.file import FileReadStream
from faststream.nats import NatsBroker
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.infra.db.transaction import transaction
from papilio.infra.http.connection import HTTPConnection
from pydantic import HttpUrl
from sqlmodel import col

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.configs.infra.pg.repositories.storage import (
    StorageConfigRepository,
)
from src.apps.core.storage.files.app.interfaces.uploads import IFileUpload
from src.apps.core.storage.files.domain.dtos.uploads import FileUpload
from src.apps.shop.billing.ocr_requests.app.interfaces.processing import (
    IOCRPipeline,
)
from src.apps.shop.billing.ocr_requests.domain.parsers.receipts import fields
from src.apps.shop.billing.ocr_requests.infra.pg.repositories.crud import (
    OCRRequestRepository,
)
from src.apps.shop.billing.payments.app.interfaces.commands import (
    IPaymentCommand,
)
from src.apps.shop.billing.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)
from src.bootstrap.events import create_events
from src.settings.config import CoreSettings, NatsConfig, OCRConfig

pytestmark = pytest.mark.integration


def test_receipt_fields() -> None:
    result = fields(
        (
            "مبلغ: ۱۲۳٬۴۵۶ تومان",
            "کد رهگیری: ۰۰۰۴۲",
            "شماره مرجع: ۴۲۰۰۰",
        )
    )
    assert result.amount == 1_234_560
    assert result.tracking_code == "00042"
    assert result.reference_code == "42000"
    assert fields(("مبلغ: ۱۲۳۴۵۶",)).amount is None
    assert fields(("مبلغ: ۱۰۰ ریال", "مبلغ: ۱۲۳ تومان")).amount is None


async def test_ocr_without_endpoint(settings: CoreSettings) -> None:
    settings.nats = NatsConfig(servers=["nats://127.0.0.1:4222"])
    app = create_events(settings)
    try:
        broker = app.registrar.broker.native
        assert isinstance(broker, NatsBroker)
        assert not broker.subscribers
    finally:
        await app.stop()


async def test_ocr_pipeline(pg: CoreSettings, tmp_path: Path) -> None:
    pg.storage.path = str(tmp_path / "media")
    pg.storage.temp_dir = str(tmp_path / "staging")
    pg.storage.public_base_url = HttpUrl("https://media.example.org/ocr/")
    pg.nats = NatsConfig(servers=["nats://127.0.0.1:4222"])
    pg.ocr = OCRConfig(url=HttpUrl("http://paddleocr.test/ocr"))
    app = create_events(pg)
    container = app.container
    image = b"receipt bytes for the controlled OCR peer"
    calls: list[Request] = []

    async def recognize(request: Request) -> Response:
        calls.append(request)
        body = json.loads(request.content)
        assert request.url == "http://paddleocr.test/ocr"
        assert b64decode(body["file"]) == image
        assert body["fileType"] == 1 and not body["visualize"]
        if len(calls) == 2:
            return Response(503)
        return Response(
            200,
            json={
                "errorCode": 0,
                "result": {
                    "ocrResults": [
                        {
                            "prunedResult": {
                                "rec_texts": [
                                    "مبلغ: ۱۲۳ تومان",
                                    "کد رهگیری: ۰۰۰۴۲",
                                ],
                                "rec_scores": [0.99, 0.6]
                                if len(calls) == 1
                                else [0.99],
                            }
                        }
                    ],
                },
            },
        )

    try:
        connection = await container.get(HTTPConnection)
        await connection.client.aclose()
        connection.client = AsyncClient(transport=MockTransport(recognize))
        async with container() as scope:
            configs = await scope.get(StorageConfigRepository)
            async with transaction():
                previous = await configs.get_backend()
                selected = await configs.save(StorageBackend.LOCAL)
        try:
            path = tmp_path / "original.png"
            path.write_bytes(image)
            uploads = await container.get(IFileUpload)
            async with await FileReadStream.from_path(path) as source:
                upload = await uploads.upload(
                    source,
                    FileUpload(original_name=path.name, mime_type="image/png"),
                    max_bytes=1024,
                )
            async with container() as scope:
                command = await scope.get(IPaymentCommand)
                payment = await command.create(
                    PaymentCreate(amount=2_000, image_url=upload.url)
                )
            try:
                pipeline = await container.get(IOCRPipeline)
                await pipeline.process(
                    payment.receipt_id, event_id="ocr-example-1"
                )
                await pipeline.process(
                    payment.receipt_id, event_id="ocr-example-1"
                )
                assert len(calls) == 1

                async with container() as scope:
                    requests = await scope.get(OCRRequestRepository)
                    receipts = await scope.get(ReceiptRepository)
                    attempt = await requests.get_one(
                        col(requests.table.event_id) == "ocr-example-1"
                    )
                    receipt = await receipts.get_by_id(payment.receipt_id)
                    assert attempt is not None and receipt is not None
                    assert (
                        attempt.status
                        == receipt.extraction_status
                        == ExtractionStatus.EXTRACTED
                    )
                    assert receipt.amount == 1_230
                    assert (
                        receipt.tracking_code is None
                        and receipt.paid_at is None
                    )

                for event_id, error_code in (
                    ("ocr-example-2", "ocr_api_unavailable"),
                    ("ocr-example-3", "ocr_response_invalid"),
                ):
                    await pipeline.process(
                        payment.receipt_id, event_id=event_id
                    )
                    async with container() as scope:
                        requests = await scope.get(OCRRequestRepository)
                        receipts = await scope.get(ReceiptRepository)
                        payments = await scope.get(PaymentRepository)
                        attempt = await requests.get_one(
                            col(requests.table.event_id) == event_id
                        )
                        receipt = await receipts.get_by_id(payment.receipt_id)
                        stored = await payments.get_by_id(payment.id)
                        assert attempt is not None and receipt is not None
                        assert (
                            attempt.status
                            == receipt.extraction_status
                            == ExtractionStatus.FAILED
                        )
                        assert attempt.error_code == error_code
                        assert receipt.amount == 1_230
                        assert (
                            stored is not None
                            and stored.status == payment.status
                        )
            finally:
                async with container() as scope:
                    requests = await scope.get(OCRRequestRepository)
                    receipts = await scope.get(ReceiptRepository)
                    payments = await scope.get(PaymentRepository)
                    async with transaction():
                        await requests.remove(
                            col(requests.table.receipt_id)
                            == payment.receipt_id
                        )
                        await payments.remove_by_id(payment.id)
                        await receipts.remove_by_id(payment.receipt_id)
        finally:
            async with container() as scope:
                configs = await scope.get(StorageConfigRepository)
                async with transaction():
                    if previous is None:
                        await configs.remove_by_id(selected.id)
                    else:
                        await configs.save(previous)
    finally:
        await app.stop()
