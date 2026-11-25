"""Verify Plisio settlement against the exact original quote."""

from asyncio import sleep, wait_for
from contextlib import AsyncExitStack
from datetime import timedelta
from decimal import Decimal
from os import environ
from secrets import token_hex
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork, UnitOfWork
from papilio.infra.http.connection import HTTPConnection
from sqlalchemy import insert

from src.apps.shop.crypto.gateways.app.commands.configs import (
    GatewayConfigCommand,
)
from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig
from src.apps.shop.crypto.gateways.domain.dtos.records import GatewayCreate
from src.apps.shop.crypto.payments.app.commands.create import (
    PaymentCreateCommand,
)
from src.apps.shop.crypto.payments.app.commands.quote import (
    PaymentQuoteCommand,
)
from src.apps.shop.crypto.payments.app.interfaces.services import (
    ICryptoPaymentService,
)
from src.apps.shop.crypto.payments.app.pipelines.check import (
    PaymentCheckPipeline,
)
from src.apps.shop.crypto.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.crypto.payments.domain.errors import CheckUnavailable
from src.apps.shop.crypto.payments.domain.results.invoice import Invoice
from src.apps.shop.crypto.payments.infra.pg.tables import CryptoPaymentTable
from src.settings.config import CoreSettings, NatsConfig, SchedulerConfig

pytestmark = pytest.mark.integration
SECRET = "test-check-invoice-secret"


async def _gateway(container: AsyncContainer) -> int:
    async with container() as scope:
        gateways = await scope.get(ICryptoGatewayService)
        configs = await scope.get(GatewayConfigCommand)
        gateway = await gateways.create(
            GatewayCreate(kind="plisio", title="Check Invoice", is_active=True)
        )
        await configs.save(
            gateway.id,
            PlisioConfig.model_validate(
                {
                    "kind": "plisio",
                    "api_url": "https://api.plisio.net/api/v1",
                    "api_key": SECRET,
                }
            ),
        )
    return gateway.id


async def _payment(container: AsyncContainer, invoice_id: str) -> int:
    gateway_id = await _gateway(container)
    async with container() as scope:
        create = await scope.get(PaymentCreateCommand)
        quote = await scope.get(PaymentQuoteCommand)
        payments = await scope.get(ICryptoPaymentService)
        payment = await create.create(
            PaymentCreate(gateway_id=gateway_id, amount=1_220_000)
        )
        await quote.quote(payment.id, max_age=timedelta(minutes=2))
        async with transaction():
            await payments.set_invoice(
                payment.id,
                Invoice(
                    invoice_id, f"https://plisio.net/invoice/{invoice_id}"
                ),
            )
    return payment.id


@pytest.mark.parametrize("switched", [False, True])
async def test_check_plisio_payment(
    app: FastAPI,
    client: AsyncClient,
    switched: bool,
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    payment_id = await _payment(container, "root-invoice")
    pipeline = await container.get(PaymentCheckPipeline)
    connection = await container.get(HTTPConnection)
    original = connection.client
    calls: list[str] = []
    status = "pending"
    order_number = str(payment_id)
    quote = {"source_amount": "1220000", "source_currency": "IRR"}
    received = "0.00009"
    parent = "root-invoice"
    fail = False

    def plisio(request: Request) -> Response:
        assert UnitOfWork.current() is None
        assert request.method == "GET"
        assert request.url.host == "api.plisio.net"
        assert dict(request.url.params) == {"api_key": SECRET}
        path = request.url.path.removeprefix("/api/v1/operations/")
        calls.append(path)
        if fail:
            return Response(503)
        root = switched and path == "root-invoice"
        return Response(
            200,
            json={
                "status": "success",
                "data": {
                    "type": "invoice",
                    "id": path,
                    "status": "cancelled duplicate" if root else status,
                    "parent_id": parent if path == "child-invoice" else None,
                    "child_ids": ["child-invoice"] if root else [],
                    "sum": "0.00009",
                    "actual_sum": received,
                    "params": {"order_number": order_number, **quote},
                },
            },
        )

    async with AsyncClient(transport=MockTransport(plisio)) as upstream:
        connection.client = upstream
        try:
            pending = await pipeline.check(payment_id)
            assert pending.confirmed_at is None
            status = "completed"
            if switched:
                parent = "foreign-invoice"
                assert (await pipeline.check(payment_id)).confirmed_at is None
                parent = "root-invoice"

            order_number = str(payment_id + 1)
            assert (await pipeline.check(payment_id)).confirmed_at is None
            order_number = str(payment_id)
            quote["source_amount"] = "1220001"
            assert (await pipeline.check(payment_id)).confirmed_at is None
            quote["source_amount"] = "1220000"
            quote["source_currency"] = "USD"
            assert (await pipeline.check(payment_id)).confirmed_at is None
            quote["source_currency"] = "IRR"
            received = "0.00008"
            assert (await pipeline.check(payment_id)).confirmed_at is None
            received = "0.00009"
            fail = True
            with pytest.raises(CheckUnavailable):
                await pipeline.check(payment_id)
            fail = False
            confirmed = await pipeline.check(payment_id)
            assert confirmed.confirmed_at is not None
            assert confirmed.settlement_id == (
                "child-invoice" if switched else "root-invoice"
            )
            assert confirmed.invoice_id == "root-invoice"
            assert confirmed.quote_amount == Decimal("1220000")

            before = len(calls)
            replay = await pipeline.check(payment_id)
            assert replay.confirmed_at == confirmed.confirmed_at
            assert len(calls) == before
        finally:
            connection.client = original


async def test_scheduled_plisio_batch(pg: CoreSettings) -> None:
    pytest.importorskip("taskiq_nats")
    from taskiq.receiver import Receiver

    from src.bootstrap.scheduler import create_scheduler

    url = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not url:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to an isolated broker")
    suffix = token_hex(6)
    pg.nats = NatsConfig(servers=[url])
    pg.scheduler = SchedulerConfig(
        stream=f"payments_{suffix}",
        subject=f"payments.{suffix}",
        durable=f"payments_{suffix}",
        rate_refresh_interval=None,
    )

    broker, beat = create_scheduler(pg)
    broker.is_worker_process = True
    active = peak = 0
    calls: list[str] = []
    ids: dict[str, int] = {}

    async def plisio(request: Request) -> Response:
        nonlocal active, peak
        assert UnitOfWork.current() is None
        assert request.url.host == "api.plisio.net"
        assert request.url.params["api_key"] == SECRET
        invoice = request.url.path.rsplit("/", 1)[-1]
        calls.append(invoice)
        active += 1
        peak = max(peak, active)
        try:
            await sleep(0.025)
            if invoice == "batch-0":
                return Response(503)
            return Response(
                200,
                json={
                    "status": "success",
                    "data": {
                        "type": "invoice",
                        "id": invoice,
                        "status": "completed",
                        "sum": "0.00009",
                        "actual_sum": "0.00009",
                        "params": {
                            "order_number": str(ids[invoice]),
                            "source_amount": "1220000",
                            "source_currency": "IRR",
                        },
                    },
                },
            )
        finally:
            active -= 1

    async with AsyncExitStack() as stack:
        stack.push_async_callback(broker.shutdown)
        await broker.startup()
        selections = []
        for source in beat.sources:
            await source.startup()
            stack.push_async_callback(source.shutdown)
            for schedule in await source.get_schedules():
                if schedule.task_name == "shop.crypto.payments.recheck.v1":
                    selections.append((source, schedule))
        [(source, schedule)] = selections
        assert schedule.kwargs["query"] == {
            "limit": 100,
            "delay": 300,
            "concurrency": 8,
        }

        container = cast(AsyncContainer, broker.state.papilio_container)
        gateway_id = await _gateway(container)
        async with container() as scope:
            unit = await scope.get(PGUnitOfWork)
            table = CryptoPaymentTable.__table__
            stmt = insert(table).returning(table.c.invoice_id, table.c.id)
            async with transaction():
                result = await unit.execute(
                    stmt,
                    [
                        {
                            "gateway_id": gateway_id,
                            "amount": 1_220_000,
                            "quote_amount": Decimal("1220000"),
                            "quote_currency": "IRR",
                            "invoice_id": f"batch-{number}",
                            "invoice_url": f"https://plisio.net/invoice/batch-{number}",
                        }
                        for number in range(103)
                    ],
                )
                ids.update((invoice, id) for invoice, id in result.tuples())

        connection = await container.get(HTTPConnection)
        original = connection.client
        upstream = await stack.enter_async_context(
            AsyncClient(transport=MockTransport(plisio))
        )
        connection.client = upstream
        stack.callback(setattr, connection, "client", original)

        receiver = Receiver(broker, run_startup=False, max_async_tasks=1)
        messages = broker.listen()
        stack.push_async_callback(messages.aclose)
        for count in (100, 103, 103):
            await beat.on_ready(source, schedule)
            message = await wait_for(anext(messages), timeout=5)
            await receiver.callback(message)
            assert len(calls) == count

        assert 1 < peak <= 8
        assert len(set(calls)) == 103
        async with container() as scope:
            payments = await scope.get(ICryptoPaymentService)
            async with transaction():
                failed = await payments.get_by_id(ids["batch-0"])
                confirmed = await payments.get_by_id(ids["batch-102"])
            assert failed.confirmed_at is None
            assert failed.last_check_at is not None
            assert confirmed.settlement_id == "batch-102"
