"""Check payment policy and webhook key management through the panel API."""

from asyncio import create_subprocess_exec, gather, sleep, wait_for
from contextlib import suppress
from datetime import timedelta
from json import loads
from os import environ
from pathlib import Path
from secrets import randbelow
from sys import executable
from typing import cast

import pytest
import yaml
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.core.config import RedisConfig
from papilio.infra.db.transaction import transaction
from papilio.infra.redis.client import RedisClient, resolve
from papilio.utils.dates import utc_now

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.billing.deposits.app.commands.match import (
    DepositMatchCommand,
)
from src.apps.shop.billing.deposits.domain.models.records import DepositModel
from src.apps.shop.billing.payment_settings.app.interfaces.services import (
    IPaymentSettingsService,
)
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.bootstrap.events import create_events
from src.settings.config import CoreSettings, NatsConfig

pytestmark = pytest.mark.integration
SETTINGS = "/admin/payment-settings"
CACHE_KEY = "shop:payment-settings:v2"


@pytest.fixture
def pg(pg: CoreSettings) -> CoreSettings:
    url = environ.get("PAPILIOVPN_TEST_REDIS_URL")
    if url:
        pg.redis = RedisConfig(
            url=url,
            max_connections=2,
            socket_timeout=1,
            socket_connect_timeout=1,
            health_check_interval=0,
        )
    return pg


@pytest.fixture
async def billing_admin(app: FastAPI, client: AsyncClient) -> dict[str, str]:
    password = "isolated-settings-admin-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        suffix = randbelow(10**7)
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key=f"payment-settings-{suffix}", title="Billing")
        )
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Billing",
                last_name="Settings",
                mobile=f"0912{suffix:07d}",
                password=password,
                role_id=role.id,
            ),
            super_admin=True,
        )
    response = await client.post(
        "/admin/auth/tokens",
        json={"mobile": user.mobile, "password": password},
    )
    assert response.status_code == 200, response.text
    return {
        "Authorization": f"Bearer {response.json()['data']['access_token']}"
    }


async def test_payment_settings(
    app: FastAPI, client: AsyncClient, billing_admin: dict[str, str]
) -> None:
    assert (await client.get(SETTINGS)).status_code == 401
    response = await client.get(SETTINGS, headers=billing_admin)
    assert response.status_code == 200, response.text
    assert response.json()["data"] == {
        "auto_confirm": False,
        "digits": 5,
        "window_hours": 24,
        "has_key": False,
    }

    container = cast(AsyncContainer, app.state.dishka_container)
    redis = await container.get(RedisClient | None)
    if redis is not None:
        assert await resolve(redis.client.exists(CACHE_KEY))

    invalid = await client.put(
        SETTINGS,
        headers=billing_admin,
        json={"auto_confirm": True, "digits": 2},
    )
    assert invalid.status_code == 422
    updated = await client.put(
        SETTINGS,
        headers=billing_admin,
        json={"auto_confirm": True, "digits": 3, "window_hours": 6},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["digits"] == 3
    if redis is not None:
        assert not await resolve(redis.client.exists(CACHE_KEY))

    issued = await client.post(f"{SETTINGS}/key", headers=billing_admin)
    assert issued.status_code == 201, issued.text
    key = issued.json()["data"]["key"]
    assert len(key) >= 32

    current = await client.get(SETTINGS, headers=billing_admin)
    assert key not in current.text
    if redis is not None:
        raw = await resolve(redis.client.get(CACHE_KEY))
        assert raw is not None and "key_hash" not in loads(raw)
    assert current.json()["data"] == {
        "auto_confirm": True,
        "digits": 3,
        "window_hours": 6,
        "has_key": True,
    }

    async with container() as scope:
        service = await scope.get(IPaymentSettingsService)
        revoked = await service.revoke_key()
    assert revoked.key_hash is None
    assert revoked.auto_confirm is True
    if redis is not None:
        assert not await resolve(redis.client.exists(CACHE_KEY))
    assert (await client.get(SETTINGS, headers=billing_admin)).json()["data"][
        "has_key"
    ] is False
    await client.put(
        SETTINGS,
        headers=billing_admin,
        json={"auto_confirm": False, "digits": 5, "window_hours": 24},
    )


async def test_automatic_payment(
    app: FastAPI, client: AsyncClient, billing_admin: dict[str, str]
) -> None:
    payments = "/admin/payments"
    hook = "/hooks/deposits"
    container = cast(AsyncContainer, app.state.dishka_container)

    async def dispatch(id: int) -> DepositModel:
        async with container() as scope:
            command = await scope.get(DepositMatchCommand)
            deposit = await command.match(id)
        return deposit

    settings = {"auto_confirm": True, "digits": 3, "window_hours": 1}
    response = await client.put(SETTINGS, headers=billing_admin, json=settings)
    assert response.status_code == 200
    try:
        issued = await client.post(f"{SETTINGS}/key", headers=billing_admin)
        assert issued.status_code == 201
        key = issued.json()["data"]["key"]
        headers = {"X-API-Key": key}
        earlier = 109_999
        before_issue = await client.post(
            hook, headers=headers, json={"amount": earlier}
        )
        assert before_issue.status_code == 201
        await dispatch(before_issue.json()["data"]["id"])

        created = []
        responses = await gather(
            client.post(
                payments, headers=billing_admin, json={"amount": 110_000}
            ),
            client.post(
                payments, headers=billing_admin, json={"amount": 110_000}
            ),
        )
        for response in responses:
            assert response.status_code == 201, response.text
            payment = response.json()["data"]
            assert payment["amount"] == 110_000
            assert payment["receipt_id"] is None
            assert payment["status"] == "pending"
            assert payment["auto_confirm"] is True
            assert payment["transfer_amount"] != payment["amount"]
            assert payment["transfer_amount"] != earlier
            assert payment["confirmation_code"] == (
                f"{payment['transfer_amount'] % 1_000:03d}"
            )
            created.append(payment)

        first, second = created
        assert first["transfer_amount"] != second["transfer_amount"]
        payload = {"amount": first["transfer_amount"]}
        assert (await client.post(hook, json=payload)).status_code == 401
        assert (
            await client.post(hook, headers=headers, json={"amount": 0})
        ).status_code == 422

        old = await client.post(
            hook,
            headers=headers,
            json={**payload, "paid_at": "2000-01-01T00:00:00Z"},
        )
        assert old.status_code == 201, old.text
        assert old.json()["data"]["payment_id"] is None
        await dispatch(old.json()["data"]["id"])

        await client.put(
            SETTINGS,
            headers=billing_admin,
            json={"auto_confirm": True, "digits": 5},
        )
        attempts = await gather(
            client.post(hook, headers=headers, json=payload),
            client.post(hook, headers=headers, json=payload),
        )
        assert all(result.status_code == 201 for result in attempts)
        records = [result.json()["data"] for result in attempts]
        assert all(record["payment_id"] is None for record in records)
        initial = await client.get(
            f"{payments}/{first['id']}", headers=billing_admin
        )
        assert initial.json()["data"]["payment"]["status"] == "pending"

        results = await gather(*(dispatch(record["id"]) for record in records))
        (linked,) = [
            deposit for deposit in results if deposit.payment_id == first["id"]
        ]
        replayed = await dispatch(linked.id)
        assert replayed.id == linked.id
        assert replayed.payment_id == first["id"]
        async with container() as scope:
            repo = await scope.get(PaymentRepository)
            async with transaction():
                await repo.update_by_id(
                    second["id"],
                    {"created_at": utc_now() - timedelta(hours=2)},
                )
        expired = await client.post(
            hook, headers=headers, json={"amount": second["transfer_amount"]}
        )
        assert expired.status_code == 201
        expired_id = expired.json()["data"]["id"]
        unmatched = await dispatch(expired_id)
        assert unmatched.id == expired_id
        assert unmatched.payment_id is None
        checked = await client.get(
            f"/admin/deposits/{expired_id}", headers=billing_admin
        )
        assert checked.json()["data"]["payment_id"] is None
        detail = await client.get(
            f"{payments}/{first['id']}", headers=billing_admin
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["data"]["receipt"] is None
        updated = detail.json()["data"]["payment"]
        assert updated["status"] == "confirmed"
        assert updated["confirmed_at"] is not None

        history = await client.get(
            "/admin/deposits",
            headers=billing_admin,
            params={"payment_id": first["id"]},
        )
        assert history.status_code == 200, history.text
        (matched,) = history.json()["data"]
        assert matched["id"] == linked.id

        await client.put(
            SETTINGS,
            headers=billing_admin,
            json={"auto_confirm": False, "digits": 5, "window_hours": 24},
        )
        disabled = await client.post(
            hook, headers=headers, json={"amount": second["transfer_amount"]}
        )
        assert disabled.status_code == 201
        assert disabled.json()["data"]["payment_id"] is None
        await dispatch(disabled.json()["data"]["id"])
        reviewed = await client.patch(
            f"{payments}/{second['id']}/review",
            headers=billing_admin,
            json={"status": "confirmed"},
        )
        assert reviewed.status_code == 200

        manual = await client.post(
            payments,
            headers=billing_admin,
            json={"amount": 110_000, "image_url": "/media/manual.jpg"},
        )
        assert manual.status_code == 201, manual.text
        assert manual.json()["data"]["auto_confirm"] is False
        assert manual.json()["data"]["transfer_amount"] is None

        await client.delete(f"{SETTINGS}/key", headers=billing_admin)
        revoked = await client.post(hook, headers=headers, json=payload)
        assert revoked.status_code == 401
    finally:
        await client.put(
            SETTINGS,
            headers=billing_admin,
            json={"auto_confirm": False, "digits": 5, "window_hours": 24},
        )
        await client.delete(f"{SETTINGS}/key", headers=billing_admin)


async def test_deposit_event(
    pg: CoreSettings,
    client: AsyncClient,
    billing_admin: dict[str, str],
    tmp_path: Path,
) -> None:
    url = environ.get("PAPILIOVPN_TEST_NATS_URL")
    if not url:
        pytest.skip("Set PAPILIOVPN_TEST_NATS_URL to isolated JetStream")
    pg.nats = NatsConfig(servers=[url])
    events = create_events(pg)
    config = tmp_path / "relay.yml"
    config.write_text(yaml.safe_dump(pg.model_dump(mode="json")))
    worker = None
    await events.start()
    try:
        await client.put(
            SETTINGS,
            headers=billing_admin,
            json={"auto_confirm": True, "digits": 5, "window_hours": 24},
        )
        issued = await client.post(f"{SETTINGS}/key", headers=billing_admin)
        key = issued.json()["data"]["key"]
        created = await client.post(
            "/admin/payments", headers=billing_admin, json={"amount": 618_000}
        )
        payment = created.json()["data"]
        received = await client.post(
            "/hooks/deposits",
            headers={"X-API-Key": key},
            json={"amount": payment["transfer_amount"]},
        )
        assert received.status_code == 201, received.text
        deposit = received.json()["data"]
        assert deposit["payment_id"] is None

        worker = await create_subprocess_exec(
            str(Path(executable).with_name("faststream")),
            "run",
            "src.entrypoints.outbox:app",
            env={**environ, "PAPILIO_CONFIG": str(config)},
        )
        for _ in range(120):
            report = await client.get(
                f"/admin/deposits/{deposit['id']}", headers=billing_admin
            )
            if report.json()["data"]["payment_id"] == payment["id"]:
                break
            await sleep(0.1)
        else:
            pytest.fail("Bank event did not link the payment")
    finally:
        if worker is not None:
            with suppress(ProcessLookupError):
                worker.terminate()
            try:
                await wait_for(worker.wait(), timeout=5)
            except TimeoutError:
                worker.kill()
                await worker.wait()
        await events.stop()
        await client.put(
            SETTINGS,
            headers=billing_admin,
            json={"auto_confirm": False, "digits": 5, "window_hours": 24},
        )
        await client.delete(f"{SETTINGS}/key", headers=billing_admin)
