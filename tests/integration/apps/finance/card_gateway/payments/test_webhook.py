"""Authenticate Variza and confirm a tracked payment only once."""

from asyncio import gather
from datetime import timedelta
from hmac import digest
from json import dumps, loads
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, Response
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork
from papilio.utils.dates import utc_now
from papilio_tasks.apps.outbox import OutboxWriter
from pydantic import SecretStr
from sqlalchemy import select
from sqlmodel import col

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.finance.card_gateway.gateways.app.interfaces.configs import (
    IConfigService,
    IGatewayConfigCodec,
)
from src.apps.finance.card_gateway.gateways.domain.dtos.configs import (
    VarizaConfig,
)
from src.apps.finance.card_gateway.gateways.domain.enums.records import (
    GatewayKind,
)
from src.apps.finance.card_gateway.gateways.domain.models.configs import (
    ConfigModel,
)
from src.apps.finance.card_gateway.gateways.domain.models.records import (
    GatewayModel,
)
from src.apps.finance.card_gateway.gateways.infra.pg.repositories.crud import (
    GatewayRepository,
)
from src.apps.finance.card_gateway.payments.domain.models.records import (
    PaymentModel,
)
from src.apps.finance.card_gateway.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.finance.card_gateway.payments.infra.pg.tables import (
    CardGatewayDeliveryTable,
)
from src.bootstrap.outbox import pending

pytestmark = pytest.mark.integration
SECRET = b"variza-webhook-fixture-secret"
CONFIRMED = "papiliovpn.finance.card_gateway.payment.confirmed.v1"


async def post_notice(
    client: AsyncClient,
    hook: str,
    delivery_id: str,
    **changes: object,
) -> Response:
    payload = {
        "event": "payment.paid",
        "status": "paid",
        "slug": "issued-link",
        "attempt_code": "00071",
        "base_amount": 120_000,
        "amount": 120_128,
        "sent_at": utc_now().isoformat(),
    }
    body = dumps(payload | changes, indent=2).encode()
    signature = "sha256=" + digest(SECRET, body, "sha256").hex()
    response = await client.post(
        hook,
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Delivery-Id": delivery_id,
        },
    )
    return response


@pytest.fixture
async def webhook_payment(
    app: FastAPI, client: AsyncClient
) -> tuple[AsyncContainer, int, int]:
    container = cast(AsyncContainer, app.state.dishka_container)
    codec = await container.get(IGatewayConfigCodec)
    config = codec.seal(
        VarizaConfig(
            api_key=SecretStr("isolated-webhook-api-key"),
            webhook_secret=SecretStr(SECRET.decode()),
        )
    )
    assert config is not None
    async with container() as scope:
        gateways = await scope.get(GatewayRepository)
        configs = await scope.get(IConfigService)
        payments = await scope.get(PaymentRepository)
        async with transaction():
            gateway = await gateways.create(
                GatewayModel(
                    title="Webhook account",
                    kind=GatewayKind.VARIZA,
                )
            )
            await configs.create(ConfigModel(key=gateway.kind, config=config))
            payment = await payments.create(
                PaymentModel(
                    gateway_id=gateway.id,
                    amount=1_200_000,
                    slug="issued-link",
                    pay_url="https://variza.ir/pay/issued-link",
                    expires_at=utc_now() + timedelta(minutes=30),
                )
            )
        gateway_id, payment_id = gateway.id, payment.id
    return container, gateway_id, payment_id


async def test_confirm_and_read_variza_payment(
    app: FastAPI,
    client: AsyncClient,
    webhook_payment: tuple[AsyncContainer, int, int],
) -> None:
    container, gateway_id, payment_id = webhook_payment
    detail = f"/admin/card-gateway/payments/{payment_id}"
    hook = f"/hooks/card-gateway/variza/{gateway_id}"
    assert (await client.get(detail)).status_code == 401

    async def admin() -> AdminIdentity:
        return AdminIdentity(
            1, 1, {"finance": AdminPermission.READ}, uuid4(), False
        )

    app.dependency_overrides[current_admin] = admin
    waiting = await client.get(detail)
    assert waiting.status_code == 200, waiting.text
    assert waiting.json()["data"]["status"] == "pending"

    denied = await client.post(
        hook,
        content=b'{"event":"payment.paid"}',
        headers={"X-Delivery-Id": "invalid", "X-Webhook-Signature": "bad"},
    )
    assert denied.status_code == 401, denied.text
    oversized = await client.post(
        hook,
        content=b"x" * (16 * 1024 + 1),
        headers={"X-Delivery-Id": "oversized"},
    )
    assert oversized.status_code == 413, oversized.text
    unmatched = await post_notice(
        client, hook, "mismatch", base_amount=120_001
    )
    assert unmatched.status_code == 200, unmatched.text
    assert (await client.get(detail)).json()["data"]["status"] == "pending"

    accepted = await gather(
        post_notice(client, hook, "paid"),
        post_notice(client, hook, "paid"),
        post_notice(client, hook, "other-delivery"),
    )
    assert [response.status_code for response in accepted] == [200, 200, 200]

    saved = (await client.get(detail)).json()["data"]
    assert saved["status"] == "confirmed"
    assert saved["amount"] == 1_200_000
    assert saved["paid_amount"] == 1_201_280
    assert saved["attempt_code"] == "00071"

    async with container() as scope:
        unit = await scope.get(PGUnitOfWork)
        events = await unit.execute(
            select(pending.c.payload).where(pending.c.queue == CONFIRMED)
        )
        payloads = [loads(event)["event"] for event in events.scalars()]
        assert payloads.count({"payment_id": payment_id}) == 1
        delivered = await unit.execute(
            select(col(CardGatewayDeliveryTable.delivery_id)).where(
                col(CardGatewayDeliveryTable.gateway_id) == gateway_id
            )
        )
        assert sorted(delivered.scalars()) == [
            "mismatch",
            "other-delivery",
            "paid",
        ]


async def test_confirmation_rolls_back_when_outbox_fails(
    client: AsyncClient,
    webhook_payment: tuple[AsyncContainer, int, int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    container, gateway_id, payment_id = webhook_payment
    hook = f"/hooks/card-gateway/variza/{gateway_id}"
    with monkeypatch.context() as patch:
        patch.setattr(
            OutboxWriter,
            "append",
            AsyncMock(side_effect=RuntimeError("fixture outbox error")),
        )
        with pytest.raises(RuntimeError, match="fixture outbox error"):
            await post_notice(client, hook, "rollback")

    async with container() as scope:
        repo = await scope.get(PaymentRepository)
        payment = await repo.get_by_id(payment_id)
        assert payment is not None and payment.confirmed_at is None

    replay = await post_notice(client, hook, "rollback")
    assert replay.status_code == 200, replay.text
    async with container() as scope:
        repo = await scope.get(PaymentRepository)
        payment = await repo.get_by_id(payment_id)
        assert payment is not None and payment.confirmed_at is not None


async def test_late_notice_is_recorded_for_review(
    client: AsyncClient,
    webhook_payment: tuple[AsyncContainer, int, int],
) -> None:
    container, gateway_id, payment_id = webhook_payment
    async with container() as scope:
        repo = await scope.get(PaymentRepository)
        async with transaction():
            await repo.update_by_id(
                payment_id, {"expires_at": utc_now() - timedelta(minutes=1)}
            )
    hook = f"/hooks/card-gateway/variza/{gateway_id}"
    response = await post_notice(client, hook, "late")
    assert response.status_code == 200, response.text

    async with container() as scope:
        repo = await scope.get(PaymentRepository)
        payment = await repo.get_by_id(payment_id)
        assert payment is not None and payment.confirmed_at is None
        unit = await scope.get(PGUnitOfWork)
        recorded = await unit.execute(
            select(col(CardGatewayDeliveryTable.paid_amount)).where(
                col(CardGatewayDeliveryTable.gateway_id) == gateway_id,
                col(CardGatewayDeliveryTable.delivery_id) == "late",
            )
        )
        assert recorded.scalar_one() == 1_201_280
