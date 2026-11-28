"""Exercise the pinned SDK, stored bank evidence and scheduled verification."""

from asyncio import wait_for
from contextlib import AsyncExitStack
from json import loads
from os import environ
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork, UnitOfWork
from payment_gateways_sdk import NetworkError
from sqlalchemy import select
from taskiq.receiver import Receiver

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.finance.ipg.gateways.domain.enums.records import GatewayKind
from src.apps.finance.ipg.payments.app.interfaces.create import (
    ICreatePaymentCommand,
)
from src.apps.finance.ipg.payments.app.pipelines.verify import VerifyPipeline
from src.apps.finance.ipg.payments.domain.dtos.records import PaymentCreate
from src.apps.finance.ipg.payments.domain.dtos.verify import VerifyPolicy
from src.apps.finance.ipg.payments.domain.enums.records import LinkStatus
from src.apps.finance.ipg.payments.domain.results.verify import VerifyBatch
from src.apps.finance.ipg.payments.infra.broker.config import BrokerConfig
from src.apps.finance.ipg.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.bootstrap.outbox import pending
from src.bootstrap.scheduler import create_scheduler
from src.settings.config import CoreSettings, NatsConfig, SchedulerConfig

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("kind", list(GatewayKind))
async def test_create_and_verify_ipg_payment(
    app: FastAPI,
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    pg: CoreSettings,
    kind: GatewayKind,
) -> None:
    async def admin() -> AdminIdentity:
        grants = (
            AdminPermission.CREATE
            | AdminPermission.READ
            | AdminPermission.UPDATE
        )
        return AdminIdentity(1, 1, {"finance": grants}, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    merchant = "fcd1226a-fd39-45dc-b547-cb7a485f8504"
    created = await client.post(
        "/admin/ipg/gateways",
        json={
            "kind": kind,
            "title": "Fixture active gateway",
            "is_active": True,
            "config": {"merchant_id": merchant},
        },
    )
    assert created.status_code == 201, created.text
    gateway_id = created.json()["data"]["id"]

    data = PaymentCreate.model_validate(
        {
            "kind": kind,
            "amount": 123_456,
            "description": "Fixture purchase",
            "callback_url": f"https://merchant.example/callbacks/ipg/{kind}",
        }
    )
    authority = "A00000000000000000000000000012345678"
    reference = authority if kind is GatewayKind.ZARINPAL else "12345678"
    callback_ref = (
        authority[:-1] + "9" if kind is GatewayKind.ZARINPAL else "12345679"
    )
    tracking_code = "804320"
    order_ids: list[str] = []
    verifications: list[str] = []

    async def provider(
        url: str, payload: dict[str, object], **_options: object
    ) -> dict[str, object]:
        assert UnitOfWork.current() is None
        merchant_field = (
            "merchant_id" if kind is GatewayKind.ZARINPAL else "merchant"
        )
        assert payload[merchant_field] == merchant
        if url.endswith(("/request", "/request.json")):
            callback = (
                "callback_url"
                if kind is GatewayKind.ZARINPAL
                else "callbackUrl"
            )
            assert payload["amount"] == data.amount
            assert payload["description"] == data.description
            assert payload[callback] == str(data.callback_url)
            metadata = cast(dict[str, object], payload.get("metadata", {}))
            order_ids.append(
                str(payload.get("orderId") or metadata["order_id"])
            )
            if len(order_ids) == 2:
                raise NetworkError("Fixture lost redirect response")
            token = reference if len(order_ids) == 1 else callback_ref
            if kind is GatewayKind.ZARINPAL:
                return {"data": {"code": 100, "authority": token}}
            return {"result": 100, "trackId": int(token)}

        verifications.append(url)
        if kind is GatewayKind.ZARINPAL:
            assert payload["authority"] in {reference, callback_ref}
            assert payload["amount"] == data.amount
            return {"data": {"code": 100, "ref_id": int(tracking_code)}}

        token = str(payload["trackId"])
        assert token in {reference, callback_ref}
        order_id = order_ids[0] if token == reference else order_ids[2]
        if url.endswith("/inquiry"):
            return {
                "result": 100,
                "status": 2,
                "amount": data.amount,
                "orderId": order_id,
            }
        assert url.endswith("/verify")
        return {
            "result": 100,
            "amount": data.amount,
            "refNumber": int(tracking_code),
            "orderId": order_id,
        }

    monkeypatch.setattr(
        f"payment_gateways_sdk.gateways.{kind}.async_engine.apost_json",
        provider,
    )
    container = cast(AsyncContainer, app.state.dishka_container)
    command = await container.get(ICreatePaymentCommand)
    issued = await command.create(data)
    unknown = await command.create(data)
    callback = await command.create(data)
    assert order_ids == [str(issued.id), str(unknown.id), str(callback.id)]
    assert issued.status is LinkStatus.READY and issued.reference == reference
    assert issued.url is not None and issued.url.endswith(f"/{reference}")
    assert unknown.status is LinkStatus.UNKNOWN and unknown.url is None

    rotated = await client.put(
        f"/admin/ipg/gateways/{gateway_id}/config",
        json={"merchant_id": "sandbox-rotated-merchant"},
    )
    assert rotated.status_code == 200, rotated.text
    callback_path = f"/callbacks/ipg/{kind}"
    accepted, failed = (
        (
            {"Authority": callback_ref, "Status": "OK"},
            {"Authority": callback_ref, "Status": "NOK"},
        )
        if kind is GatewayKind.ZARINPAL
        else (
            {"trackId": callback_ref, "success": "1"},
            {"trackId": callback_ref, "success": "0"},
        )
    )
    assert (await client.get(callback_path, params=failed)).status_code == 204
    assert not verifications
    for _ in range(2):
        reply = await client.get(callback_path, params=accepted)
        assert reply.status_code == 204, reply.text

    pipeline = await container.get(VerifyPipeline)
    policy = VerifyPolicy(
        limit=1, parallel=1, retry_seconds=600, window_minutes=60
    )
    nats = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if nats and kind is GatewayKind.ZIBAL:
        await run_scheduled_verification(pg, nats)
    else:
        assert await pipeline.run(policy) == VerifyBatch(
            selected=1, confirmed=1
        )
    assert await pipeline.run(policy) == VerifyBatch(selected=0, confirmed=0)
    assert len(verifications) == (2 if kind is GatewayKind.ZARINPAL else 4)

    detail = await client.get(f"/admin/ipg/payments/{issued.id}")
    assert detail.status_code == 200, detail.text
    view = detail.json()["data"]
    assert view["status"] == "confirmed"
    assert view["reference"] == reference
    assert view["tracking_code"] == tracking_code
    assert view["confirmed_at"] is not None
    assert "credential" not in view

    async with container() as scope:
        payments = await scope.get(PaymentRepository)
        unresolved = await payments.get_by_id(unknown.id)
        unit = await scope.get(PGUnitOfWork)
        events = await unit.execute(
            select(pending.c.payload).where(
                pending.c.queue == BrokerConfig.confirmed
            )
        )
        payloads = [loads(event)["event"] for event in events.scalars()]
    assert unresolved is not None and unresolved.status is LinkStatus.UNKNOWN
    assert payloads.count({"payment_id": issued.id}) == 1
    assert payloads.count({"payment_id": callback.id}) == 1


async def run_scheduled_verification(
    settings: CoreSettings, nats: str
) -> None:
    """Send the registered schedule to the native worker."""
    suffix = uuid4().hex
    settings.nats = NatsConfig(servers=[nats])
    settings.scheduler = SchedulerConfig(
        stream=f"ipg_verify_{suffix}",
        subject=f"ipg.verify.{suffix}",
        durable=f"ipg_verify_{suffix}",
    )
    broker, beat = create_scheduler(settings)
    broker.is_worker_process = True
    async with AsyncExitStack() as stack:
        stack.push_async_callback(broker.shutdown)
        await broker.startup()
        schedules = []
        for source in beat.sources:
            await source.startup()
            stack.push_async_callback(source.shutdown)
            schedules.extend(
                (source, schedule)
                for schedule in await source.get_schedules()
                if schedule.task_name == BrokerConfig.verify_task
            )
        [(source, schedule)] = schedules
        assert schedule.interval == 60
        assert schedule.kwargs["policy"]["limit"] == 100
        messages = broker.listen()
        stack.push_async_callback(messages.aclose)
        await beat.on_ready(source, schedule)
        wire = await wait_for(anext(messages), timeout=4)
        receiver = Receiver(broker, run_startup=False, max_async_tasks=1)
        await wait_for(receiver.callback(wire), timeout=4)
