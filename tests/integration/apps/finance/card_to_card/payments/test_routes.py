"""Verify Finance permissions and the manual payment review routes."""

from datetime import timedelta
from json import loads
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork
from papilio.utils.dates import utc_now
from sqlalchemy import delete, select

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.finance.card_to_card.payments.app.interfaces import commands
from src.apps.finance.card_to_card.payments.app.interfaces.services import (
    ICardPaymentService,
)
from src.apps.finance.card_to_card.payments.domain.dtos.records import (
    CardPaymentCreate,
)
from src.apps.finance.card_to_card.payments.domain.dtos.review import (
    CardPaymentReview,
)
from src.apps.finance.card_to_card.payments.domain.enums.records import (
    PaymentMode,
    PaymentStatus,
)
from src.apps.finance.card_to_card.payments.domain.models.records import (
    CardPaymentModel,
)
from src.apps.finance.card_to_card.payments.infra.pg.repositories.crud import (
    CardPaymentRepository,
)
from src.apps.shop.banking.banks.domain.models.records import BankModel
from src.apps.shop.banking.banks.infra.pg.repositories.records import (
    BankRepository,
)
from src.apps.shop.banking.payment_cards.domain.models.records import (
    PaymentCardModel,
)
from src.apps.shop.banking.payment_cards.infra.pg.repositories.crud import (
    PaymentCardRepository,
)
from src.bootstrap.outbox import pending

pytestmark = pytest.mark.integration
PAYMENTS = "/admin/card-payments"
CONFIRMED = "papiliovpn.finance.card_to_card.payment.confirmed.v1"
REJECTED = "papiliovpn.finance.card_to_card.payment.rejected.v1"


async def test_card_payment_routes(app: FastAPI, client: AsyncClient) -> None:
    assert (await client.get(PAYMENTS)).status_code == 401

    scopes: dict[str, int] = {
        "shop": AdminPermission.READ | AdminPermission.UPDATE
    }

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, scopes, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    assert (await client.get(PAYMENTS)).status_code == 403
    scopes["finance"] = AdminPermission.READ

    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        banks = await scope.get(BankRepository)
        cards = await scope.get(PaymentCardRepository)
        async with transaction():
            bank = await banks.create(
                BankModel(code="finance_routes", title="Finance Routes")
            )
            card = await cards.create(
                PaymentCardModel(
                    bank_id=bank.id,
                    card_number="0000000000000001",
                    holder_name="Test Holder",
                )
            )
        command = await scope.get(commands.IManualPaymentCommand)
        first = await command.create(
            CardPaymentCreate(
                card_id=card.id, amount=120_000, receipt_url="/media/first.png"
            )
        )
        second = await command.create(
            CardPaymentCreate(
                card_id=card.id,
                amount=130_000,
                receipt_url="/media/second.png",
            )
        )

    event_ids: list[int] = []
    auto_id: int | None = None
    expired_id: int | None = None
    try:
        params = {"status": "pending", "card_id": card.id, "per_page": 1}
        response = await client.get(PAYMENTS, params=params)
        assert response.status_code == 200, response.text
        body = response.json()
        assert [item["id"] for item in body["data"]] == [second.id]
        assert body["meta"]["total_items"] == 2
        oldest = await client.get(PAYMENTS, params={**params, "page": 2})
        assert [item["id"] for item in oldest.json()["data"]] == [first.id]
        assert (
            await client.get(PAYMENTS, params={"per_page": 101})
        ).status_code == 422

        path = f"{PAYMENTS}/{second.id}"
        detail = await client.get(path)
        assert detail.status_code == 200, detail.text
        record = detail.json()["data"]
        assert record["card_id"] == card.id
        assert record["receipt_url"] == "/media/second.png"
        assert record["amount"] == 130_000
        assert record["mode"] == "manual"
        assert record["payable_amount"] is None
        assert record["code"] is None
        assert record["expires_at"] is None
        assert (await client.get(f"{PAYMENTS}/{2**63 - 1}")).status_code == 404

        decision = {"status": "rejected", "reason": "Amount mismatch"}
        assert (
            await client.patch(f"{path}/review", json=decision)
        ).status_code == 403
        scopes["finance"] |= AdminPermission.UPDATE
        reviewed = await client.patch(f"{path}/review", json=decision)
        assert reviewed.status_code == 200, reviewed.text
        record = reviewed.json()["data"]
        assert record["status"] == "rejected"
        assert record["rejection_reason"] == "Amount mismatch"
        assert record["decided_at"] is not None
        assert (
            await client.patch(f"{path}/review", json={"status": "confirmed"})
        ).status_code == 409
        remaining = await client.get(PAYMENTS, params=params)
        assert [item["id"] for item in remaining.json()["data"]] == [first.id]
        confirmed = await client.patch(
            f"{PAYMENTS}/{first.id}/review", json={"status": "confirmed"}
        )
        assert confirmed.status_code == 200, confirmed.text
        assert confirmed.json()["data"]["status"] == "confirmed"

        async with container() as scope:
            payments = await scope.get(ICardPaymentService)
            auto = await payments.create_auto(
                card_id=card.id,
                amount=120_000,
                payable_amount=120_007,
                code="0007",
                expires_at=utc_now() + timedelta(minutes=30),
            )
            auto_id = auto.id
            assert auto.expires_at is not None
            assert auto.created_at is not None
            repo = await scope.get(CardPaymentRepository)
            async with transaction():
                expired = await repo.create(
                    CardPaymentModel(
                        card_id=card.id,
                        mode=PaymentMode.AUTO,
                        amount=120_000,
                        payable_amount=120_007,
                        code="0007",
                        created_at=utc_now() - timedelta(hours=1),
                        expires_at=utc_now() - timedelta(minutes=30),
                    )
                )
                expired_id = expired.id
            since = auto.created_at.isoformat()
            until = (auto.created_at + timedelta(minutes=1)).isoformat()
            review = await scope.get(commands.IReviewPaymentCommand)
            with pytest.raises(RuntimeError, match="rollback review"):
                async with transaction():
                    await review.review(
                        auto_id,
                        CardPaymentReview(status=PaymentStatus.CONFIRMED),
                    )
                    raise RuntimeError("rollback review")
            unit = await scope.get(PGUnitOfWork)
            result = await unit.execute(
                select(pending.c.id, pending.c.queue, pending.c.payload)
                .where(pending.c.queue.in_((CONFIRMED, REJECTED)))
                .order_by(pending.c.id)
            )
            outcomes = []
            for row in result:
                data = loads(row.payload)["event"]
                if data["payment_id"] in (first.id, second.id, auto_id):
                    event_ids.append(row.id)
                    outcomes.append((row.queue, data))
            assert outcomes == [
                (REJECTED, {"payment_id": second.id}),
                (CONFIRMED, {"payment_id": first.id}),
            ]

        detail = await client.get(f"{PAYMENTS}/{auto_id}")
        assert detail.status_code == 200, detail.text
        record = detail.json()["data"]
        assert record["mode"] == "auto"
        assert record["payable_amount"] == 120_007
        assert record["code"] == "0007"
        assert record["expires_at"] is not None
        assert record["status"] == "pending"

        filters = {
            "mode": "auto",
            "card_id": card.id,
            "status": "pending",
            "code": "0007",
            "amount": 120_000,
            "payable_amount": 120_007,
        }
        for extra, expected in (
            ({"expired": "false"}, [auto_id]),
            ({"expired": "true"}, [expired_id]),
            ({"since": since, "until": until}, [auto_id]),
            ({"code": "0008"}, []),
            ({"payable_amount": 120_008}, []),
            ({"transfer_id": 2**63 - 1}, []),
        ):
            matches = await client.get(PAYMENTS, params=filters | extra)
            assert matches.status_code == 200, matches.text
            assert [item["id"] for item in matches.json()["data"]] == expected
            assert matches.json()["meta"]["total_items"] == len(expected)
        paged = await client.get(
            PAYMENTS, params=filters | {"per_page": 1, "page": 2}
        )
        assert [item["id"] for item in paged.json()["data"]] == [auto_id]
        assert paged.json()["meta"]["total_items"] == 2
        open_window = await client.get(
            PAYMENTS, params={"expired": "false", "card_id": card.id}
        )
        assert [item["id"] for item in open_window.json()["data"]] == [auto_id]
        assert (
            await client.get(PAYMENTS, params={"since": until, "until": since})
        ).status_code == 400
        assert (
            await client.get(PAYMENTS, params={"code": "7"})
        ).status_code == 422
        assert (await client.post(PAYMENTS, json={})).status_code == 405
    finally:
        app.dependency_overrides.pop(current_admin, None)
        async with container() as scope:
            repo = await scope.get(CardPaymentRepository)
            cards = await scope.get(PaymentCardRepository)
            banks = await scope.get(BankRepository)
            unit = await scope.get(PGUnitOfWork)
            async with transaction():
                if auto_id is not None:
                    await repo.remove_by_id(auto_id)
                if expired_id is not None:
                    await repo.remove_by_id(expired_id)
                await repo.remove_by_ids([first.id, second.id])
                await cards.remove_by_id(card.id)
                await banks.remove_by_id(bank.id)
                if event_ids:
                    await unit.execute(
                        delete(pending).where(pending.c.id.in_(event_ids))
                    )
