"""Exercise receipt OCR with a controlled PaddleOCR response."""

import json
from base64 import b64decode
from pathlib import Path

import pytest
from anyio.streams.file import FileReadStream
from faststream.nats import NatsBroker
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.errors.exceptions import NotFoundException
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
from src.apps.shop.billing.ocr_requests.app.interfaces.services import (
    IOCRRequestService,
)
from src.apps.shop.billing.ocr_requests.app.parsers.receipts import (
    ReceiptParser,
)
from src.apps.shop.billing.ocr_requests.domain.dtos.records import (
    OCRRequestList,
)
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
    parse = ReceiptParser().parse
    result = parse(
        (
            "مبلغ: ۱۲۳٬۴۵۶ تومان",
            "کد رهگیری: ۰۰۰۴۲",
            "شماره مرجع: ۴۲۰۰۰",
        )
    )
    assert result.amount == 1_234_560
    assert result.tracking_code == "00042"
    assert result.reference_code == "42000"
    assert parse(("مبلغ: ۱۲۳۴۵۶",)).amount is None
    assert parse(("مبلغ: ۱۰۰ ریال", "مبلغ: ۱۲۳ تومان")).amount is None
    assert parse(("مبلغ", "۲،۴۰۰،۰۰۰ ریال")).amount == 2_400_000
    assert parse(("ریال ۲٬۴۰۰٬۰۰۰", "مبلغ انتقال")).amount == 2_400_000
    assert parse(("مبلغ", "۲٬۴۰۰٬۰۰۰۰ ریال")).amount is None
    assert parse(("مبلغ", "", "۲٬۴۰۰٬۰۰۰ ریال")).amount is None
    assert parse(("۲٬۴۰۰٬۰۰۰ ریال",)).amount is None
    assert parse(("۱۰۰ ریال", "مبلغ", "۲۰۰ ریال")).amount is None


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
    reads = {
        1: (
            ["مبلغ", "۱۲۳ تومان", "کد رهگیری: ۰۰۰۴۲"],
            [0.99, 0.99, 0.6],
        ),
        3: (["مبلغ: ۱۲۳ تومان", "کد رهگیری: ۰۰۰۴۲"], [0.99]),
        4: (["مبلغ: ۲۴،۰۰۰،۰۰۰ ریال"], [0.6]),
        5: (["مبلغ", "ناخوانا", "۲۴،۰۰۰،۰۰۰ ریال"], [0.99, 0.6, 0.99]),
    }

    async def recognize(request: Request) -> Response:
        calls.append(request)
        body = json.loads(request.content)
        assert request.url == "http://paddleocr.test/ocr"
        assert b64decode(body["file"]) == image
        assert body["fileType"] == 1 and not body["visualize"]
        assert body["textRecScoreThresh"] == 0
        if len(calls) == 2:
            response = Response(503)
        else:
            texts, scores = reads[len(calls)]
            response = Response(
                200,
                json={
                    "errorCode": 0,
                    "result": {
                        "ocrResults": [
                            {
                                "prunedResult": {
                                    "rec_texts": texts,
                                    "rec_scores": scores,
                                }
                            }
                        ],
                    },
                },
            )
        return response

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
                    requests = await scope.get(IOCRRequestService)
                    receipts = await scope.get(ReceiptRepository)
                    attempt = await requests.find_by_event("ocr-example-1")
                    receipt = await receipts.get_by_id(payment.receipt_id)
                    assert attempt is not None and receipt is not None
                    assert (await requests.get_by_id(attempt.id)).event_id == (
                        attempt.event_id
                    )
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
                        requests = await scope.get(IOCRRequestService)
                        receipts = await scope.get(ReceiptRepository)
                        payments = await scope.get(PaymentRepository)
                        attempt = await requests.find_by_event(event_id)
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

                for event_id in ("ocr-example-4", "ocr-example-5"):
                    await pipeline.process(
                        payment.receipt_id, event_id=event_id
                    )
                    async with container() as scope:
                        requests = await scope.get(IOCRRequestService)
                        receipts = await scope.get(ReceiptRepository)
                        attempt = await requests.find_by_event(event_id)
                        receipt = await receipts.get_by_id(payment.receipt_id)
                        assert attempt is not None and receipt is not None
                        assert (
                            attempt.status
                            == receipt.extraction_status
                            == ExtractionStatus.UNREADABLE
                        )
                        assert receipt.amount == 1_230

                async with container() as scope:
                    requests = await scope.get(IOCRRequestService)
                    for page, event_id in (
                        (1, "ocr-example-3"),
                        (2, "ocr-example-2"),
                    ):
                        failed = await requests.list(
                            OCRRequestList(
                                receipt_id=payment.receipt_id,
                                status=ExtractionStatus.FAILED,
                                per_page=1,
                                page=page,
                            )
                        )
                        assert failed.total_items == 2
                        assert [
                            attempt.event_id for attempt in failed.items
                        ] == [event_id]
                    assert await requests.find_by_event("ocr-missing") is None
                    with pytest.raises(NotFoundException):
                        await requests.get_by_id(2**63 - 1)
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
