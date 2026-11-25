"""Manage crypto gateways through the Shop administrator API."""

from decimal import Decimal
from json import loads
from os import environ
from secrets import randbelow
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.core.config import RedisConfig
from papilio.infra.redis.client import RedisClient, resolve
from papilio.security.crypto import decrypt

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.crypto.gateways.infra.pg.repositories.configs import (
    CryptoGatewayConfigRepository,
)
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration


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


async def test_gateways(app: FastAPI, client: AsyncClient) -> None:
    path = "/admin/crypto-gateways"
    suffix = randbelow(10**7)
    password = "isolated-gateway-test-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key=f"gateways-{suffix}", title="Gateways")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Gateway",
                last_name="Operator",
                mobile=f"0932{suffix:07d}",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.is_success, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }
    assert (await client.get(path)).status_code == 401
    assert (await client.get(f"{path}/1/config")).status_code == 401
    data = {
        "key": f"account-{suffix}",
        "title": "Example Gateway",
        "icon_url": "/media/gateway.webp",
        "kind": "plisio",
        "price_currency": "EUR",
        "pay_currency": "USDT_TRON",
        "rial_rate": "1250000.125",
    }
    invalid = await client.post(
        path, headers=headers, json={**data, "rial_rate": "0"}
    )
    assert invalid.status_code == 422
    created = await client.post(path, headers=headers, json=data)
    assert created.status_code == 201, created.text
    record = created.json()["data"]
    assert record["is_active"] is False
    assert record["kind"] == "plisio"
    assert record["icon_url"] == data["icon_url"]
    assert record["pay_currency"] == "USDT_TRON"
    assert Decimal(str(record["rial_rate"])) == Decimal("1250000.125")
    detail = f"{path}/{record['id']}"
    assert (
        await client.post(path, headers=headers, json=data)
    ).status_code == 409
    assert (await client.get(detail, headers=headers)).json()["data"] == record
    assert (
        await client.patch(detail, headers=headers, json={})
    ).status_code == 400

    updated = await client.patch(
        detail, headers=headers, json={"is_active": True, "pay_currency": None}
    )
    assert updated.is_success, updated.text
    changed = updated.json()["data"]
    assert changed["pay_currency"] is None
    assert changed["price_currency"] == "EUR"
    assert changed["is_active"] is True
    assert changed["icon_url"] == data["icon_url"]
    for q, count in (("example", 1), ("%%", 0)):
        page = await client.get(
            path,
            headers=headers,
            params={"q": q, "kind": "plisio", "is_active": True},
        )
        assert page.is_success, page.text
        assert page.json()["meta"]["total_items"] == count
        assert len(page.json()["data"]) == count
    batch = await client.get(
        f"{path}/batch",
        headers=headers,
        params={"ids": [record["id"], record["id"]]},
    )
    assert batch.is_success, batch.text
    assert [row["id"] for row in batch.json()["data"]] == [record["id"]]
    cleared = await client.patch(
        detail, headers=headers, json={"icon_url": None}
    )
    assert cleared.json()["data"]["icon_url"] is None

    config_path = f"{detail}/config"
    assert (await client.get(config_path, headers=headers)).status_code == 404
    config = {
        "kind": "plisio",
        "api_url": "https://api.plisio.net/api/v1",
        "callback_base_url": "https://shop.example.test",
        "api_key": "test-gateway-credential",
        "price_decimals": 2,
    }
    invalid_url = await client.put(
        config_path,
        headers=headers,
        json={**config, "api_url": "https://unrelated.example.test"},
    )
    assert invalid_url.status_code == 422
    assert config["api_key"] not in invalid_url.text
    wrong_kind = await client.put(
        config_path,
        headers=headers,
        json={
            **config,
            "kind": "nowpayments",
            "api_url": "https://api.nowpayments.io/v1",
            "ipn_secret": "test-unrelated-ipn-key",
        },
    )
    assert wrong_kind.status_code == 409
    updated_config = await client.put(
        config_path, headers=headers, json=config
    )
    assert updated_config.status_code == 200, updated_config.text
    assert config["api_key"] not in updated_config.text
    view = updated_config.json()["data"]
    assert view["has_api_key"] is True
    assert view["has_ipn_secret"] is False
    assert (await client.get(config_path, headers=headers)).json()[
        "data"
    ] == view

    redis = await container.get(RedisClient | None)
    cache_key = f"shop:crypto-gateways:config:{record['id']}"
    if redis is not None:
        raw = await resolve(redis.client.get(cache_key))
        assert raw is not None and "test-gateway-credential" not in str(raw)
        assert "api_key" not in loads(raw)

    rotated = await client.put(
        config_path,
        headers=headers,
        json={
            **config,
            "api_key": "test-gateway-replacement",
            "price_decimals": 4,
        },
    )
    assert rotated.status_code == 200, rotated.text
    if redis is not None:
        assert not await resolve(redis.client.exists(cache_key))
    fresh = await client.get(config_path, headers=headers)
    assert fresh.json()["data"]["price_decimals"] == 4
    async with container() as scope:
        repo = await scope.get(CryptoGatewayConfigRepository)
        stored = await repo.find_by_gateway_id(record["id"])
        assert stored is not None
        ciphertext = stored.config["api_key"]
        assert isinstance(ciphertext, str)
        assert ciphertext != "test-gateway-replacement"
        assert decrypt(ciphertext, "test-only-gateway-encryption-key") == (
            "test-gateway-replacement"
        )

    removed = await client.delete(detail, headers=headers)
    assert removed.is_success, removed.text
    assert removed.json()["data"]["id"] == record["id"]
    assert (await client.get(detail, headers=headers)).status_code == 404
    assert (await client.get(config_path, headers=headers)).status_code == 404
    if redis is not None:
        assert not await resolve(redis.client.exists(cache_key))
