"""Verify the admin enqueue and native scheduled dispatch end to end."""

from asyncio import wait_for
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from decimal import Decimal
from os import environ
from secrets import randbelow
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.redis.client import RedisClient, resolve

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.crypto.rates.app.interfaces.cache import IRateCache
from src.apps.shop.crypto.rates.domain.models.records import Rate
from src.settings.config import CoreSettings, NatsConfig, SchedulerConfig

pytestmark = pytest.mark.integration
RATES = "/admin/crypto-rates"
PATH = f"{RATES}/refresh"


async def _headers(
    app: FastAPI, client: AsyncClient, *, super_admin: bool
) -> dict[str, str]:
    container = cast(AsyncContainer, app.state.dishka_container)
    suffix = randbelow(10**7)
    password = "rate-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key=f"rate-{suffix}", title="Rates Operator")
        )
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Rates",
                last_name="Operator",
                mobile=f"0917{suffix:07d}",
                role_id=role.id,
                password=password,
            ),
            super_admin=super_admin,
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": user.mobile, "password": password},
    )
    assert login.is_success, login.text
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@asynccontextmanager
async def _use_client(
    connection: HTTPConnection, client: AsyncClient
) -> AsyncIterator[None]:
    old = connection.client
    connection.client = client
    try:
        yield
    finally:
        connection.client = old


async def test_refresh_without_job_transport(
    app: FastAPI, client: AsyncClient
) -> None:
    assert (await client.post(PATH)).status_code == 401
    headers = await _headers(app, client, super_admin=True)
    response = await client.post(PATH, headers=headers)
    assert response.status_code == 503, response.text


@pytest.mark.parametrize(
    ("override", "interval"),
    [
        ({}, 20),
        ({"rate_refresh_interval": None}, None),
        ({"rate_refresh_interval": 37}, 37),
    ],
)
async def test_refresh_jobs(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    override: dict[str, int | None],
    interval: int | None,
) -> None:
    pytest.importorskip("taskiq_nats")
    from taskiq.receiver import Receiver

    from src.bootstrap.scheduler import create_scheduler

    url = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not url or pg.redis is None:
        pytest.skip("Set isolated test Redis and NATS URLs")
    suffix = randbelow(10**7)
    pg.nats = NatsConfig(servers=[url])
    pg.scheduler = SchedulerConfig.model_validate(
        {
            "stream": f"rates_{suffix}",
            "subject": f"rates.{suffix}",
            "durable": f"rates_{suffix}",
            **override,
        }
    )

    calls = 0

    def market(request: Request) -> Response:
        nonlocal calls
        calls += 1
        assert str(request.url) == "https://api.wallex.ir/v1/markets"
        return Response(
            200,
            json={
                "success": True,
                "result": {
                    "symbols": {
                        "USDTTMN": {
                            "baseAsset": "USDT",
                            "quoteAsset": "TMN",
                            "stats": {"lastPrice": str(60000 + calls)},
                        }
                    }
                },
            },
        )

    broker, beat = create_scheduler(pg)
    broker.is_worker_process = True
    async with AsyncExitStack() as stack:
        stack.push_async_callback(broker.shutdown)
        await broker.startup()
        for source in beat.sources:
            await source.startup()
            stack.push_async_callback(source.shutdown)
        worker = cast(AsyncContainer, broker.state.papilio_container)
        api = cast(AsyncContainer, app.state.dishka_container)
        upstream = await stack.enter_async_context(
            AsyncClient(transport=MockTransport(market))
        )
        for container in (api, worker):
            http = await container.get(HTTPConnection)
            await stack.enter_async_context(_use_client(http, upstream))
        cache = await worker.get(IRateCache)
        redis = await worker.get(RedisClient | None)
        assert redis is not None
        await resolve(redis.client.hdel("shop:crypto:rates", "USD"))

        deny = await _headers(app, client, super_admin=False)
        assert (await client.post(PATH, headers=deny)).status_code == 403
        assert (await client.get(RATES)).status_code == 401
        assert (await client.get(RATES, headers=deny)).status_code == 403
        headers = await _headers(app, client, super_admin=True)
        empty = await client.get(RATES, headers=headers)
        assert empty.status_code == 200, empty.text
        assert empty.json()["data"] == []
        queued = await client.post(PATH, headers=headers)
        assert queued.status_code == 202, queued.text
        assert calls == 0
        assert await cache.find("USD") is None

        receiver = Receiver(broker, run_startup=False, max_async_tasks=1)
        messages = broker.listen()
        stack.push_async_callback(messages.aclose)
        message = await wait_for(anext(messages), timeout=3)
        wire = message if isinstance(message, bytes) else message.data
        task = broker.formatter.loads(wire)
        assert task.task_id == queued.json()["data"]["task_id"]
        assert task.args == [] and task.kwargs == {}
        await receiver.callback(message)
        rate = await cache.find("USD")
        assert isinstance(rate, Rate) and rate.rial_rate == Decimal("600010")
        current = await client.get(RATES, headers=headers)
        assert current.status_code == 200, current.text
        assert current.headers["cache-control"] == "no-store"
        assert current.json()["data"] == [
            {
                "currency": "USD",
                "rial_rate": "600010",
                "source": "wallex_usdt",
                "fetched_at": rate.fetched_at.isoformat().replace(
                    "+00:00", "Z"
                ),
            }
        ]
        assert calls == 1

        schedules = [
            (source, schedule)
            for source in beat.sources
            for schedule in await source.get_schedules()
            if schedule.task_name == task.task_name
        ]
        if interval is None:
            assert schedules == []
        else:
            [(source, schedule)] = schedules
            assert schedule.interval == interval
            await beat.on_ready(source, schedule)
            scheduled = await wait_for(anext(messages), timeout=3)
            await receiver.callback(scheduled)
            rate = await cache.find("USD")
            assert isinstance(rate, Rate) and rate.rial_rate == Decimal(
                "600020"
            )
            updated = await client.get(RATES, headers=headers)
            assert updated.status_code == 200, updated.text
            assert updated.json()["data"][0]["rial_rate"] == "600020"
            assert calls == 2
