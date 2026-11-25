"""Review payments and register their events through the admin API."""

import json
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork
from papilio_tasks.apps.outbox import OutboxWriter
from sqlalchemy import delete, select

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.billing.payments.infra.broker.config import BrokerConfig
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.billing.receipts.infra.broker.config import (
    BrokerConfig as ReceiptBrokerConfig,
)
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)
from src.bootstrap.outbox import pending

pytestmark = pytest.mark.integration
PAYMENTS = "/admin/payments"


async def test_review_requires_admin(client: AsyncClient) -> None:
    response = await client.patch(
        f"{PAYMENTS}/1/review", json={"status": "confirmed"}
    )
    assert response.status_code == 401


async def test_review_payment(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    password = "isolated-payment-review-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="payment-review", title="Payment Review")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Payment",
                last_name="Reviewer",
                mobile="09120000085",
                password=password,
                role_id=role.id,
            ),
            super_admin=True,
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }

    created: dict[int, int] = {}
    try:
        for name in ("confirm", "reject", "no-reason"):
            response = await client.post(
                PAYMENTS,
                headers=headers,
                json={"amount": 150_000, "image_url": f"/media/{name}.jpg"},
            )
            assert response.status_code == 201, response.text
            payment = response.json()["data"]
            created[payment["id"]] = payment["receipt_id"]
        confirm, reject, no_reason = created
        path = f"{PAYMENTS}/{confirm}"
        initial = await client.get(path, headers=headers)
        receipt = initial.json()["data"]["receipt"]
        assert receipt["amount"] is None

        invalid = await client.patch(
            f"{path}/review", headers=headers, json={"status": "pending"}
        )
        assert invalid.status_code == 422
        invalid = await client.patch(
            f"{path}/review",
            headers=headers,
            json={"status": "confirmed", "reason": "Unexpected reason"},
        )
        assert invalid.status_code == 400

        response = await client.patch(
            f"{path}/review", headers=headers, json={"status": "confirmed"}
        )
        assert response.status_code == 200, response.text
        payment = response.json()["data"]
        assert payment["status"] == "confirmed" and payment["confirmed_at"]
        result = await client.get(path, headers=headers)
        assert result.json()["data"]["receipt"] == receipt

        duplicate = await client.patch(
            f"{path}/review", headers=headers, json={"status": "rejected"}
        )
        assert duplicate.status_code == 409
        missing = await client.patch(
            f"{PAYMENTS}/999999/review",
            headers=headers,
            json={"status": "confirmed"},
        )
        assert missing.status_code == 404

        async def fail_append(*args: object, **kwargs: object) -> int:
            raise RuntimeError("event write failed")

        with monkeypatch.context() as patch:
            patch.setattr(OutboxWriter, "append", fail_append)
            with pytest.raises(RuntimeError, match="event write failed"):
                await client.patch(
                    f"{PAYMENTS}/{reject}/review",
                    headers=headers,
                    json={"status": "rejected", "reason": "Invalid transfer"},
                )
        result = await client.get(f"{PAYMENTS}/{reject}", headers=headers)
        payment = result.json()["data"]["payment"]
        assert (
            payment["status"] == "pending"
            and payment["rejection_reason"] is None
        )

        for payment_id, reason in (
            (reject, "Invalid transfer"),
            (no_reason, None),
        ):
            body = {"status": "rejected"}
            if reason is not None:
                body["reason"] = reason
            response = await client.patch(
                f"{PAYMENTS}/{payment_id}/review", headers=headers, json=body
            )
            assert response.status_code == 200, response.text
            payment = response.json()["data"]
            assert (
                payment["status"] == "rejected"
                and payment["confirmed_at"] is None
            )
            assert payment["rejection_reason"] == reason
            result = await client.get(
                f"{PAYMENTS}/{payment_id}", headers=headers
            )
            assert result.json()["data"]["payment"] == payment

        async with container() as scope:
            uow = await scope.get(PGUnitOfWork)
            rows = await uow.execute(
                select(pending.c.queue, pending.c.payload)
                .where(
                    pending.c.queue.in_(
                        (BrokerConfig.confirmed, BrokerConfig.rejected)
                    )
                )
                .order_by(pending.c.id)
            )
            events = []
            for queue, payload in rows.tuples():
                event = json.loads(payload)["event"]
                if event.get("payment_id") in created:
                    events.append((queue, event))
        assert events == [
            (BrokerConfig.confirmed, {"payment_id": confirm}),
            (BrokerConfig.rejected, {"payment_id": reject}),
            (BrokerConfig.rejected, {"payment_id": no_reason}),
        ]
    finally:
        async with container() as scope:
            uow = await scope.get(PGUnitOfWork)
            payments = await scope.get(PaymentRepository)
            receipts = await scope.get(ReceiptRepository)
            async with transaction():
                rows = await uow.execute(
                    select(pending.c.id, pending.c.payload).where(
                        pending.c.queue.in_(
                            (
                                BrokerConfig.confirmed,
                                BrokerConfig.rejected,
                                ReceiptBrokerConfig.created,
                            )
                        )
                    )
                )
                event_ids = []
                for event_id, payload in rows.tuples():
                    event = json.loads(payload)["event"]
                    if (
                        event.get("payment_id") in created
                        or event.get("receipt_id") in created.values()
                    ):
                        event_ids.append(event_id)
                if event_ids:
                    await uow.execute(
                        delete(pending).where(pending.c.id.in_(event_ids))
                    )
                for payment_id, receipt_id in created.items():
                    await payments.remove_by_id(payment_id)
                    await receipts.remove_by_id(receipt_id)
