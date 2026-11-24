"""Review bank receipts and persist their events through the admin API."""

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
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.billing.receipts.infra.broker.config import BrokerConfig
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)
from src.bootstrap.outbox import pending

pytestmark = pytest.mark.integration


async def test_review_requires_admin(client: AsyncClient) -> None:
    response = await client.patch(
        "/admin/receipts/1/review", json={"status": "approved"}
    )
    assert response.status_code == 401


async def test_manual_review(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    password = "isolated-receipt-review-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="receipt-review", title="Receipt Review")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Receipt",
                last_name="Reviewer",
                mobile="09120000084",
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
        for name in ("approve", "reject", "no-reason"):
            response = await client.post(
                "/admin/payments",
                headers=headers,
                json={"amount": 150_000, "image_url": f"/media/{name}.jpg"},
            )
            assert response.status_code == 201, response.text
            payment = response.json()["data"]
            created[payment["receipt_id"]] = payment["id"]
        approve, reject, no_reason = created

        response = await client.patch(
            f"/admin/receipts/{approve}/review",
            headers=headers,
            json={"status": "approved"},
        )
        assert response.status_code == 200, response.text
        receipt = response.json()["data"]
        assert receipt["status"] == "approved"
        assert receipt["amount"] is None
        payment = await client.get(
            f"/admin/payments/{created[approve]}", headers=headers
        )
        assert payment.json()["data"]["payment"]["status"] == "confirmed"
        assert payment.json()["data"]["payment"]["confirmed_at"]

        duplicate = await client.patch(
            f"/admin/receipts/{approve}/review",
            headers=headers,
            json={"status": "rejected"},
        )
        assert duplicate.status_code == 409

        async def fail_append(*args: object, **kwargs: object) -> int:
            raise RuntimeError("event write failed")

        with monkeypatch.context() as patch:
            patch.setattr(OutboxWriter, "append", fail_append)
            with pytest.raises(RuntimeError, match="event write failed"):
                await client.patch(
                    f"/admin/receipts/{reject}/review",
                    headers=headers,
                    json={
                        "status": "rejected",
                        "reason": "Unreadable receipt",
                    },
                )
        payment = await client.get(
            f"/admin/payments/{created[reject]}", headers=headers
        )
        detail = payment.json()["data"]
        assert (
            detail["payment"]["status"]
            == detail["receipt"]["status"]
            == "pending"
        )
        assert detail["receipt"]["rejection_reason"] is None

        for receipt_id, reason in (
            (reject, "Unreadable receipt"),
            (no_reason, None),
        ):
            body = {"status": "rejected"}
            if reason is not None:
                body["reason"] = reason
            response = await client.patch(
                f"/admin/receipts/{receipt_id}/review",
                json=body,
                headers=headers,
            )
            assert response.status_code == 200, response.text
            assert response.json()["data"]["rejection_reason"] == reason
            payment = await client.get(
                f"/admin/payments/{created[receipt_id]}", headers=headers
            )
            detail = payment.json()["data"]
            assert (
                detail["payment"]["status"]
                == detail["receipt"]["status"]
                == "rejected"
            )
            assert detail["payment"]["confirmed_at"] is None
            assert detail["receipt"]["rejection_reason"] == reason

        async with container() as scope:
            uow = await scope.get(PGUnitOfWork)
            rows = await uow.execute(select(pending).order_by(pending.c.id))
            events = []
            for row in rows.mappings():
                event = json.loads(row["payload"])["event"]
                if event["receipt_id"] in created:
                    events.append((row["queue"], event))
        assert events == [
            (BrokerConfig.created, {"receipt_id": receipt_id})
            for receipt_id in created
        ] + [
            (
                BrokerConfig.approved,
                {
                    "receipt_id": approve,
                    "payment_id": created[approve],
                    "actor_id": admin.id,
                },
            ),
            (
                BrokerConfig.rejected,
                {
                    "receipt_id": reject,
                    "payment_id": created[reject],
                    "actor_id": admin.id,
                    "reason": "Unreadable receipt",
                },
            ),
            (
                BrokerConfig.rejected,
                {
                    "receipt_id": no_reason,
                    "payment_id": created[no_reason],
                    "actor_id": admin.id,
                    "reason": None,
                },
            ),
        ]
    finally:
        async with container() as scope:
            uow = await scope.get(PGUnitOfWork)
            receipts = await scope.get(ReceiptRepository)
            payments = await scope.get(PaymentRepository)
            async with transaction():
                rows = await uow.execute(
                    select(pending.c.id, pending.c.payload)
                )
                ids = [
                    id
                    for id, payload in rows.tuples()
                    if json.loads(payload)["event"]["receipt_id"] in created
                ]
                if ids:
                    await uow.execute(
                        delete(pending).where(pending.c.id.in_(ids))
                    )
                for receipt_id, payment_id in created.items():
                    await payments.remove_by_id(payment_id)
                    await receipts.remove_by_id(receipt_id)
