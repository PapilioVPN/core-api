"""Exercise native billing reads against PostgreSQL."""

from datetime import UTC, datetime
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork

from src.apps.shop.billing.payments.domain.enums.records import PaymentStatus
from src.apps.shop.billing.payments.domain.models.records import PaymentModel
from src.apps.shop.billing.payments.infra.pg.readers.search import (
    PaymentReader,
)
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.billing.receipts.domain.enums.records import ReceiptStatus
from src.apps.shop.billing.receipts.domain.models.records import ReceiptModel
from src.apps.shop.billing.receipts.infra.pg.readers.search import (
    ReceiptReader,
)
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)

pytestmark = pytest.mark.integration


async def test_billing_readers(app: FastAPI) -> None:
    start = datetime(2026, 10, 1, tzinfo=UTC)
    end = datetime(2026, 10, 2, tzinfo=UTC)
    amount = 4_000_000_005
    code = "00042"

    async with app.router.lifespan_context(app):
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            uow = await scope.get(PGUnitOfWork)
            receipts = await scope.get(ReceiptRepository)
            payments = await scope.get(PaymentRepository)
            async with transaction(uow):
                first = await receipts.create(
                    ReceiptModel(
                        image_url="/media/first.jpg",
                        amount=amount,
                        tracking_code=code,
                        paid_at=start,
                    )
                )
                second = await receipts.create(
                    ReceiptModel(
                        image_url="/media/second.jpg",
                        reference_code=code,
                        paid_at=end,
                        status=ReceiptStatus.APPROVED,
                    )
                )
                assert first.id is not None and second.id is not None
                payment = await payments.create(
                    PaymentModel(
                        receipt_id=first.id, amount=amount, created_at=start
                    )
                )
                later = await payments.create(
                    PaymentModel(
                        receipt_id=second.id,
                        amount=100_000,
                        status=PaymentStatus.CONFIRMED,
                        confirmed_at=end,
                        created_at=end,
                    )
                )
                assert payment.id is not None and later.id is not None
                receipt_ids = (first.id, second.id)
                payment_ids = (payment.id, later.id)

        async with container() as scope:
            receipt_reader = await scope.get(ReceiptReader)
            payment_reader = await scope.get(PaymentReader)
            matches = await receipt_reader.search(limit=1, code=code)
            assert [row.id for row in matches.items] == [receipt_ids[1]]
            assert matches.total_items == 2
            empty = await receipt_reader.search(limit=1, offset=2, code=code)
            assert not empty.items and empty.total_items == 2
            filtered = await receipt_reader.search(
                limit=10,
                status=ReceiptStatus.PENDING,
                amount=amount,
                paid_since=start,
                paid_until=end,
            )
            assert [row.id for row in filtered.items] == [receipt_ids[0]]
            paid = await receipt_reader.search(
                limit=10, code=code, paid_since=start, paid_until=end
            )
            assert [row.id for row in paid.items] == [receipt_ids[0]]
            outside = await receipt_reader.search(limit=10, code="42")
            assert not outside.items

            page = await payment_reader.search(limit=10)
            assert [row.id for row in page.items] == list(
                reversed(payment_ids)
            )
            filtered_payments = await payment_reader.search(
                limit=10,
                status=PaymentStatus.PENDING,
                amount=amount,
                receipt_id=receipt_ids[0],
                created_since=start,
                created_until=end,
            )
            assert [row.id for row in filtered_payments.items] == [
                payment_ids[0]
            ]
            created = await payment_reader.search(
                limit=10, created_since=start, created_until=end
            )
            assert [row.id for row in created.items] == [payment_ids[0]]
            found = await payment_reader.find_by_receipt_id(receipt_ids[1])
            assert found is not None and found.id == payment_ids[1]
            assert await payment_reader.find_by_receipt_id(999_999) is None
            batch = await payment_reader.get_by_ids(
                [payment_ids[0], payment_ids[0], 999_999]
            )
            assert [row.id for row in batch] == [payment_ids[0]]
