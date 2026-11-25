"""Verify gateway account management through the panel."""

from json import loads
from os import environ
from secrets import randbelow
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.core.config import RedisConfig
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork
from papilio.infra.redis.client import RedisClient, resolve
from papilio.security.crypto import decrypt
from sqlalchemy import text

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration
BASE = "/admin/crypto-gateways"


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
async def headers(app: FastAPI, client: AsyncClient) -> dict[str, str]:
    container = cast(AsyncContainer, app.state.dishka_container)
    suffix = randbelow(10**7)
    password = "gateway-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key=f"gateway-{suffix}", title="Gateway Operator")
        )
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Gateway",
                last_name="Operator",
                mobile=f"0917{suffix:07d}",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": user.mobile, "password": password},
    )
    assert login.is_success, login.text
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


async def test_gateway_crud(
    client: AsyncClient, headers: dict[str, str]
) -> None:
    assert (await client.get(BASE)).status_code == 401
    title = f"Test {randbelow(10**8)}"
    created = await client.post(
        BASE, headers=headers, json={"kind": "plisio", "title": f"{title}%"}
    )
    assert created.status_code == 201, created.text
    row = created.json()["data"]
    assert row == {
        "id": row["id"],
        "kind": "plisio",
        "title": f"{title}%",
        "is_active": False,
        "icon_url": None,
    }
    other = await client.post(
        BASE,
        headers=headers,
        json={"kind": "plisio", "title": title},
    )
    assert other.status_code == 201, other.text
    other_id = other.json()["data"]["id"]
    assert other_id != row["id"]
    path = f"{BASE}/{row['id']}"
    listed = await client.get(
        BASE,
        headers=headers,
        params={"q": f"{title}%", "kind": "plisio", "is_active": "false"},
    )
    assert listed.is_success, listed.text
    assert listed.json()["data"] == [row]
    batch = await client.get(
        f"{BASE}/batch",
        headers=headers,
        params=[("ids", row["id"]), ("ids", row["id"]), ("ids", 9999999)],
    )
    assert batch.is_success, batch.text
    assert batch.json()["data"] == [row]
    assert (
        await client.patch(path, headers=headers, json={})
    ).status_code == 400
    assert (
        await client.patch(path, headers=headers, json={"title": None})
    ).status_code == 422
    updated = await client.patch(
        path,
        headers=headers,
        json={"is_active": True, "icon_url": "/media/icon.png"},
    )
    assert updated.is_success, updated.text
    assert updated.json()["data"]["is_active"] is True
    assert updated.json()["data"]["icon_url"] == "/media/icon.png"
    cleared = await client.patch(
        path, headers=headers, json={"icon_url": None}
    )
    assert cleared.json()["data"]["icon_url"] is None
    assert (await client.get(path, headers=headers)).json()[
        "data"
    ] == cleared.json()["data"]
    removed = await client.delete(path, headers=headers)
    assert removed.is_success, removed.text
    assert removed.json()["data"]["id"] == row["id"]
    assert (await client.get(path, headers=headers)).status_code == 404
    assert (
        await client.delete(f"{BASE}/{other_id}", headers=headers)
    ).is_success


async def test_gateway_config(
    app: FastAPI,
    pg: CoreSettings,
    client: AsyncClient,
    headers: dict[str, str],
) -> None:
    created = await client.post(
        BASE,
        headers=headers,
        json={"kind": "nowpayments", "title": "Test connection"},
    )
    assert created.is_success, created.text
    id = created.json()["data"]["id"]
    path = f"{BASE}/{id}/config"
    assert (await client.get(path, headers=headers)).status_code == 404
    values = {
        "kind": "nowpayments",
        "api_url": "https://api-sandbox.nowpayments.io/v1",
        "api_key": "test-connection-token",
        "ipn_secret": "test-signing-key",
    }
    invalid = await client.put(
        path,
        headers=headers,
        json={**values, "api_url": "http://example.test"},
    )
    assert invalid.status_code == 422
    assert values["api_key"] not in invalid.text
    mismatch = await client.put(
        path,
        headers=headers,
        json={
            "kind": "plisio",
            "api_url": "https://api.plisio.net/api/v1",
            "api_key": values["api_key"],
        },
    )
    assert mismatch.status_code == 409
    saved = await client.put(path, headers=headers, json=values)
    assert saved.is_success, saved.text
    expected = {
        "gateway_id": id,
        "kind": values["kind"],
        "api_url": values["api_url"],
        "has_api_key": True,
        "has_ipn_secret": True,
    }
    assert saved.json()["data"] == expected
    assert (await client.get(path, headers=headers)).json()["data"] == expected
    container = cast(AsyncContainer, app.state.dishka_container)
    redis = await container.get(RedisClient | None)
    key = f"shop:crypto-gateways:config:{id}"
    if redis is not None:
        raw = await resolve(redis.client.get(key))
        assert raw is not None
        assert loads(raw) == expected

    async with container() as scope:
        uow = await scope.get(PGUnitOfWork)
        async with transaction():
            stmt = text(
                "SELECT config FROM tbl_crypto_gateway_configs "
                "WHERE gateway_id = :id"
            )
            result = await uow.execute(stmt, {"id": id})
            config = result.scalar_one()
            assert pg.crypto is not None
            for name in ("api_key", "ipn_secret"):
                assert config[name] != values[name]
                assert (
                    decrypt(config[name], pg.crypto.encryption_key)
                    == values[name]
                )

    changed = await client.put(
        path,
        headers=headers,
        json={**values, "api_url": "https://api.nowpayments.io/v1"},
    )
    assert changed.is_success, changed.text
    if redis is not None:
        assert not await resolve(redis.client.exists(key))
    view = await client.get(path, headers=headers)
    assert view.json()["data"]["api_url"] == "https://api.nowpayments.io/v1"
    assert (await client.delete(f"{BASE}/{id}", headers=headers)).is_success
    assert (await client.get(path, headers=headers)).status_code == 404
