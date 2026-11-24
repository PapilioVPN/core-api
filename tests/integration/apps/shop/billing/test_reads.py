"""Read payment pages and joined receipt details through admin routes."""

from datetime import UTC, datetime
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from sqlmodel import col

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.roles.domain.dtos.role_scopes import RoleScopeCreate
from src.apps.core.access.scopes.app.interfaces.services import IScopeService
from src.apps.core.access.scopes.domain.dtos.records import ScopeCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.billing.ocr_requests.app.interfaces.services import (
    IOCRRequestService,
)
from src.apps.shop.billing.ocr_requests.domain.models.records import (
    OCRRequestModel,
)
from src.apps.shop.billing.ocr_requests.infra.pg.repositories.crud import (
    OCRRequestRepository,
)
from src.apps.shop.billing.payments.domain.enums.records import PaymentStatus
from src.apps.shop.billing.payments.domain.models.records import PaymentModel
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)
from src.apps.shop.billing.receipts.domain.models.records import ReceiptModel
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)

pytestmark = pytest.mark.integration


async def test_payment_reads(app: FastAPI, client: AsyncClient) -> None:
    path = "/admin/payments"
    history = "/admin/receipts/1/ocr-requests"
    assert (await client.get(path)).status_code == 401
    assert (await client.get(history)).status_code == 401

    password = "isolated-billing-reader-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="billing-read", title="Billing Reader")
        )
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Billing",
                last_name="Reader",
                mobile="09120000083",
                password=password,
                role_id=role.id,
            )
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": user.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }
    assert (await client.get(path, headers=headers)).status_code == 403
    assert (await client.get(history, headers=headers)).status_code == 403

    start = datetime(2026, 10, 8, tzinfo=UTC)
    end = datetime(2026, 10, 9, tzinfo=UTC)
    amount = 4_000_000_081
    async with container() as scope:
        scopes = await scope.get(IScopeService)
        grants = await scope.get(IRoleScopeService)
        receipts = await scope.get(ReceiptRepository)
        payments = await scope.get(PaymentRepository)
        requests = await scope.get(IOCRRequestService)
        async with transaction():
            existing = await scopes.find_by_key("shop")
            shop = existing or await scopes.create(
                ScopeCreate(key="shop", title="Shop")
            )
            await grants.create(
                role.id,
                RoleScopeCreate(
                    scope_id=shop.id, permissions=AdminPermission.READ
                ),
            )
            first = await receipts.create(
                ReceiptModel(
                    image_url="/media/billing-read.jpg",
                    amount=amount - 1,
                    tracking_code="00042",
                    paid_at=start,
                )
            )
            second = await receipts.create(
                ReceiptModel(image_url="/media/next.jpg")
            )
            pending = await payments.create(
                PaymentModel(
                    receipt_id=first.id, amount=amount, created_at=start
                )
            )
            confirmed = await payments.create(
                PaymentModel(
                    receipt_id=second.id,
                    amount=amount,
                    status=PaymentStatus.CONFIRMED,
                    created_at=end,
                    confirmed_at=end,
                )
            )
            failed = await requests.create(
                OCRRequestModel(
                    receipt_id=first.id,
                    event_id="billing-read-ocr-failed",
                    status=ExtractionStatus.FAILED,
                    error_code="ocr_api_unavailable",
                )
            )
            extracted = await requests.create(
                OCRRequestModel(
                    receipt_id=first.id,
                    event_id="billing-read-ocr-extracted",
                    status=ExtractionStatus.EXTRACTED,
                )
            )
            other = await requests.create(
                OCRRequestModel(
                    receipt_id=second.id,
                    event_id="billing-read-other-receipt",
                    status=ExtractionStatus.FAILED,
                )
            )

    try:
        assert (
            failed is not None and extracted is not None and other is not None
        )
        history = f"/admin/receipts/{first.id}/ocr-requests"
        result = await client.get(
            history, params={"per_page": 1}, headers=headers
        )
        assert result.status_code == 200, result.text
        attempts = result.json()
        assert [row["id"] for row in attempts["data"]] == [extracted.id]
        assert attempts["data"][0]["error_code"] is None
        assert attempts["meta"] == {
            "total_items": 2,
            "total_pages": 2,
            "has_prev": False,
            "has_next": True,
        }
        result = await client.get(
            history, params={"per_page": 1, "page": 2}, headers=headers
        )
        assert [row["id"] for row in result.json()["data"]] == [failed.id]
        result = await client.get(
            history,
            params={"status": "failed", "receipt_id": second.id},
            headers=headers,
        )
        assert result.status_code == 200, result.text
        (row,) = result.json()["data"]
        assert (
            datetime.fromisoformat(row.pop("created_at")) == failed.created_at
        )
        assert row == {
            "id": failed.id,
            "receipt_id": first.id,
            "status": "failed",
            "error_code": "ocr_api_unavailable",
        }
        result = await client.get(
            history, params={"status": "unreadable"}, headers=headers
        )
        assert result.status_code == 200 and result.json()["data"] == []
        result = await client.get(
            history, params={"page": 10**20}, headers=headers
        )
        assert result.status_code == 200 and result.json()["data"] == []
        result = await client.get(
            history, params={"status": "pending"}, headers=headers
        )
        assert result.status_code == 422
        result = await client.get(
            f"/admin/receipts/{2**63 - 1}/ocr-requests", headers=headers
        )
        assert result.status_code == 404

        blocked = await client.patch(
            f"{path}/{pending.id}/review",
            json={"status": "confirmed"},
            headers=headers,
        )
        assert blocked.status_code == 403

        result = await client.get(
            path, params={"amount": amount, "per_page": 1}, headers=headers
        )
        assert result.status_code == 200, result.text
        page = result.json()
        assert [row["id"] for row in page["data"]] == [confirmed.id]
        assert page["meta"] == {
            "total_items": 2,
            "total_pages": 2,
            "has_prev": False,
            "has_next": True,
        }
        result = await client.get(
            path,
            params={"amount": amount, "per_page": 1, "page": 2},
            headers=headers,
        )
        assert [row["id"] for row in result.json()["data"]] == [pending.id]

        result = await client.get(
            path, params={"status": "pending"}, headers=headers
        )
        assert [row["id"] for row in result.json()["data"]] == [pending.id]
        result = await client.get(
            path,
            params={
                "created_since": start.isoformat(),
                "created_until": end.isoformat(),
            },
            headers=headers,
        )
        assert [row["id"] for row in result.json()["data"]] == [pending.id]
        result = await client.get(
            path,
            params={"created_since": "2026-10-08T00:00:00"},
            headers=headers,
        )
        assert result.status_code == 422
        result = await client.get(
            path,
            params={
                "created_since": end.isoformat(),
                "created_until": start.isoformat(),
            },
            headers=headers,
        )
        assert result.status_code == 400
        assert result.json()["error"]["loc"] == ["created_until"]

        result = await client.get(f"{path}/{pending.id}", headers=headers)
        assert result.status_code == 200, result.text
        detail = result.json()["data"]
        assert detail["payment"]["amount"] == amount
        assert (
            detail["payment"]["receipt_id"]
            == detail["receipt"]["id"]
            == first.id
        )
        assert detail["receipt"]["image_url"] == first.image_url
        assert detail["receipt"]["amount"] == amount - 1
        assert detail["receipt"]["tracking_code"] == "00042"
        assert detail["receipt"]["reference_code"] is None
        assert (
            await client.get(f"{path}/999999", headers=headers)
        ).status_code == 404
        assert (await client.get(f"{path}/{pending.id}")).status_code == 401
    finally:
        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            receipts = await scope.get(ReceiptRepository)
            ocr_repo = await scope.get(OCRRequestRepository)
            scopes = await scope.get(IScopeService)
            grants = await scope.get(IRoleScopeService)
            async with transaction():
                await ocr_repo.remove(
                    col(ocr_repo.table.receipt_id).in_([first.id, second.id])
                )
                await payments.remove_by_id(pending.id)
                await payments.remove_by_id(confirmed.id)
                await receipts.remove_by_id(first.id)
                await receipts.remove_by_id(second.id)
                await grants.remove(role.id, shop.id)
                if existing is None:
                    await scopes.remove(shop.id)
