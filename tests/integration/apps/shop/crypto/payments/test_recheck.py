"""Exercise bounded crypto reconciliation through the native application."""

from datetime import timedelta
from decimal import Decimal
from secrets import token_hex
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.infra.db.transaction import active_transaction, transaction
from papilio.infra.http.connection import HTTPConnection
from papilio.utils.dates import utc_now
from pydantic import AnyUrl, SecretStr

from src.apps.shop.crypto.gateways.app.interfaces.configs import (
    ICryptoGatewayConfigService,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig
from src.apps.shop.crypto.gateways.domain.dtos.records import GatewayCreate
from src.apps.shop.crypto.payments.app.interfaces.commands import (
    ICryptoPaymentCommand,
)
from src.apps.shop.crypto.payments.domain.enums.records import (
    CryptoPaymentStatus,
)
from src.apps.shop.crypto.payments.domain.models.records import (
    CryptoPaymentModel,
)
from src.apps.shop.crypto.payments.infra.pg.repositories.crud import (
    CryptoPaymentRepository,
)
from src.settings.config import CoreSettings, NatsConfig

pytestmark = pytest.mark.integration


def test_recheck_schedule(settings: CoreSettings) -> None:
    pytest.importorskip("taskiq_nats")
    from src.bootstrap.scheduler import create_scheduler

    settings.nats = NatsConfig(servers=["nats://127.0.0.1:4222"])
    broker, _ = create_scheduler(settings)
    task = broker.find_task("shop.crypto.payments.recheck.v1")
    assert task is not None
    assert task.labels["schedule"][0]["kwargs"] == {
        "query": {"limit": 20, "delay": 300}
    }


async def test_recheck_limits_and_rotates(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    key = token_hex(4)
    async with container() as scope:
        gateways = await scope.get(ICryptoGatewayService)
        configs = await scope.get(ICryptoGatewayConfigService)
        account = await gateways.create(
            GatewayCreate(
                key=f"plisio-{key}",
                title="Plisio",
                kind="plisio",
                price_currency="USD",
                rial_rate=Decimal("500000"),
            )
        )
        other = await gateways.create(
            GatewayCreate(
                key=f"now-{key}",
                title="NOW",
                kind="nowpayments",
                price_currency="USD",
                rial_rate=Decimal("500000"),
            )
        )
        await configs.save(
            account.id,
            PlisioConfig(
                kind="plisio",
                api_url="https://api.plisio.net/api/v1",
                callback_base_url=AnyUrl("https://shop.example.test"),
                api_key=SecretStr("test-api-key"),
                price_decimals=2,
            ),
        )
        repo = await scope.get(CryptoPaymentRepository)
        now = utc_now()
        records = {}
        async with transaction():
            for name, gateway, invoice, status, age in (
                ("transient", account.id, True, "pending", 601),
                ("paid", account.id, True, "partial", 600),
                ("cancelled", account.id, True, "pending", 599),
                ("new", account.id, True, "pending", 0),
                ("no-invoice", account.id, False, "pending", 700),
                ("confirmed", account.id, True, "confirmed", 700),
                ("nowpayments", other.id, True, "pending", 700),
            ):
                records[name] = await repo.create(
                    CryptoPaymentModel(
                        gateway_id=gateway,
                        amount=1_000_000,
                        price_amount=Decimal("2"),
                        price_currency="USD",
                        status=CryptoPaymentStatus(status),
                        invoice_id=f"{key}-{name}" if invoice else None,
                        created_at=now - timedelta(seconds=age),
                    )
                )

    calls: list[str] = []

    def provider(request: Request) -> Response:
        assert active_transaction() is None
        assert request.url.host == "api.plisio.net"
        assert request.url.params["api_key"] == "test-api-key"
        invoice = request.url.path.rsplit("/", 1)[1]
        name = invoice.removeprefix(f"{key}-")
        calls.append(name)
        if name == "transient":
            response = Response(503)
        elif name == "paid":
            response = Response(
                200,
                json={
                    "status": "success",
                    "data": {
                        "type": "invoice",
                        "id": invoice,
                        "status": "cancelled duplicate",
                        "child_ids": [f"{key}-paid-child"],
                    },
                },
            )
        else:
            assert name in ("paid-child", "cancelled")
            child = name == "paid-child"
            response = Response(
                200,
                json={
                    "status": "success",
                    "data": {
                        "type": "invoice",
                        "id": invoice,
                        "status": "completed" if child else "cancelled",
                        "parent_id": f"{key}-paid" if child else None,
                        "psys_cid": "USDT_TRX",
                        "sum": "2",
                        "actual_sum": "2" if child else "0",
                        "params": {
                            "order_number": str(
                                records["paid" if child else name].id
                            ),
                            "source_amount": "2",
                            "source_currency": "USD",
                        },
                    },
                },
            )
        return response

    connection = await container.get(HTTPConnection)
    original = connection.client
    async with AsyncClient(transport=MockTransport(provider)) as upstream:
        connection.client = upstream
        try:
            async with container() as scope:
                command = await scope.get(ICryptoPaymentCommand)
                assert await command.recheck(limit=2, delay=300) == 2
                assert sorted(calls) == ["paid", "paid-child", "transient"]
                assert await command.recheck(limit=2, delay=300) == 1
                assert calls[3:] == ["cancelled"]
                assert await command.recheck(limit=2, delay=300) == 0
        finally:
            connection.client = original

    async with container() as scope:
        repo = await scope.get(CryptoPaymentRepository)
        async with transaction():
            paid = await repo.get_by_id(records["paid"].id)
            cancelled = await repo.get_by_id(records["cancelled"].id)
            transient = await repo.get_by_id(records["transient"].id)
        assert (
            paid is not None and paid.status is CryptoPaymentStatus.CONFIRMED
        )
        assert paid.provider_payment_id == f"{key}-paid-child"
        assert (
            cancelled is not None
            and cancelled.status is CryptoPaymentStatus.EXPIRED
        )
        assert (
            transient is not None
            and transient.status is CryptoPaymentStatus.PENDING
        )
