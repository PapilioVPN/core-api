"""Exercise online gateway account management through the Finance API."""

from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork
from papilio.infra.redis.client import RedisClient, resolve
from papilio.security.crypto import decrypt
from sqlalchemy import text

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration
GATEWAYS = "/admin/ipg/gateways"


async def test_manage_ipg_gateways(
    app: FastAPI, client: AsyncClient, pg: CoreSettings
) -> None:
    assert (await client.get(GATEWAYS)).status_code == 401

    grants: dict[str, int] = {"finance": AdminPermission.READ}

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, grants, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    secret = "fcd1226a-fd39-45dc-b547-cb7a485f8504"
    data = {
        "kind": "zarinpal",
        "title": "Fixture IPG primary %",
        "icon_url": "https://example.invalid/ipg.png",
        "config": {"merchant_id": secret},
    }
    assert (await client.post(GATEWAYS, json=data)).status_code == 403
    grants["finance"] |= AdminPermission.CREATE
    invalid = await client.post(GATEWAYS, json=data | {"kind": "unknown"})
    assert invalid.status_code == 422, invalid.text
    assert secret not in invalid.text
    assert (
        await client.post(
            GATEWAYS, json=data | {"config": {"merchant_id": " "}}
        )
    ).status_code == 422
    created = await client.post(GATEWAYS, json=data)
    assert created.status_code == 201, created.text
    row = created.json()["data"]
    assert row["kind"] == "zarinpal"
    assert row["title"] == data["title"]
    assert row["icon_url"] == data["icon_url"]
    assert row["is_active"] is False
    assert "config" not in row and secret not in created.text
    url = f"{GATEWAYS}/{row['id']}"
    assert (await client.get(url)).json()["data"] == row
    config_url = f"{GATEWAYS}/zarinpal/config"
    config = await client.get(config_url)
    assert config.status_code == 200, config.text
    assert config.json()["data"] == {"key": "zarinpal", "configured": True}
    container = cast(AsyncContainer, app.state.dishka_container)
    redis = await container.get(RedisClient | None)
    key = "finance:ipg:configs:v1:zarinpal"
    if redis is not None:
        raw = await resolve(redis.client.get(key))
        assert raw is not None and secret not in raw
    assert (await client.post(GATEWAYS, json=data)).status_code == 409

    second = await client.post(
        GATEWAYS,
        json=data
        | {
            "kind": "zibal",
            "title": "Fixture IPG secondary",
            "config": {"merchant_id": "fixture-zibal-merchant"},
        },
    )
    assert second.status_code == 201, second.text
    assert second.json()["data"]["kind"] == "zibal"
    assert second.json()["data"]["id"] != row["id"]

    replacement = {"merchant_id": "4ff29f13-b0a7-4a18-ab34-563e87975d26"}
    assert (
        await client.put(f"{url}/config", json=replacement)
    ).status_code == 403
    assert (
        await client.patch(url, json={"is_active": True})
    ).status_code == 403
    grants["finance"] |= AdminPermission.UPDATE
    assert (await client.patch(url, json={})).status_code == 400
    updated = await client.patch(
        url, json={"is_active": True, "icon_url": None}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["is_active"] is True
    assert updated.json()["data"]["icon_url"] is None

    query = {
        "kind": "zarinpal",
        "is_active": True,
        "q": "primary %",
        "per_page": 1,
    }
    page = await client.get(GATEWAYS, params=query)
    assert page.status_code == 200, page.text
    assert [item["id"] for item in page.json()["data"]] == [row["id"]]
    assert page.json()["meta"]["total_items"] == 1
    empty = await client.get(GATEWAYS, params={"q": "%_"})
    assert empty.status_code == 200, empty.text
    assert empty.json()["data"] == []

    rotated = await client.put(f"{url}/config", json=replacement)
    assert rotated.status_code == 200, rotated.text
    assert replacement["merchant_id"] not in rotated.text
    assert rotated.json()["data"]["is_active"] is True
    if redis is not None:
        assert await resolve(redis.client.get(key)) is None
    assert (await client.get(config_url)).json()["data"]["configured"] is True
    assert (
        await client.put(
            f"{GATEWAYS}/9223372036854775807/config", json=replacement
        )
    ).status_code == 404

    assert pg.crypto is not None
    async with container() as scope:
        uow = await scope.get(PGUnitOfWork)
        result = await uow.execute(
            text("SELECT config FROM tbl_ipg_configs WHERE key = :key"),
            {"key": "zarinpal"},
        )
        stored = result.scalar_one()
    encrypted = stored["merchant_id"]
    assert encrypted != replacement["merchant_id"]
    assert (
        decrypt(encrypted, pg.crypto.encryption_key)
        == replacement["merchant_id"]
    )
