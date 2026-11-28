"""Exercise card gateway administration on the Finance API."""

from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.redis.client import RedisClient, resolve
from papilio.security.crypto import decrypt

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.finance.card_gateway.gateways.app.interfaces.configs import (
    IConfigService,
)
from src.apps.finance.card_gateway.gateways.domain.enums.records import (
    GatewayKind,
)
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration
GATEWAYS = "/admin/card-gateways"


async def test_manage_variza_gateway(
    app: FastAPI, client: AsyncClient, pg: CoreSettings
) -> None:
    assert (await client.get(GATEWAYS)).status_code == 401

    grants: dict[str, int] = {"finance": AdminPermission.READ}

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, grants, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    config = {
        "api_key": "fixture-variza-api-key",
        "webhook_secret": "fixture-variza-webhook-secret",
        "card_last_4": "0007",
        "expires_in": "30m",
    }
    data = {
        "kind": "variza",
        "title": "Variza Gateway",
        "icon_url": "https://example.invalid/variza.png",
        "config": config,
    }

    assert (await client.post(GATEWAYS, json=data)).status_code == 403
    grants["finance"] |= AdminPermission.CREATE
    incomplete = await client.post(
        GATEWAYS,
        json=data | {"config": {"api_key": config["api_key"]}},
    )
    assert incomplete.status_code == 422, incomplete.text
    assert config["api_key"] not in incomplete.text
    for invalid in ("abc7", "۷۷۷۷"):
        rejected = await client.post(
            GATEWAYS, json=data | {"config": config | {"card_last_4": invalid}}
        )
        assert rejected.status_code == 422, rejected.text
        assert config["api_key"] not in rejected.text
        assert config["webhook_secret"] not in rejected.text

    created = await client.post(GATEWAYS, json=data)
    assert created.status_code == 201, created.text
    row = created.json()["data"]
    assert (row["kind"], row["title"], row["icon_url"]) == (
        "variza",
        data["title"],
        data["icon_url"],
    )
    assert row["is_active"] is False
    assert "config" not in row
    config_url = f"{GATEWAYS}/variza/config"
    view = await client.get(config_url)
    assert view.status_code == 200, view.text
    assert view.json()["data"] == {
        "key": "variza",
        "card_last_4": "0007",
        "expires_in": "30m",
    }
    container = cast(AsyncContainer, app.state.dishka_container)
    redis = await container.get(RedisClient | None)
    key = "finance:card_gateway:configs:v1:variza"
    if redis is not None:
        cached = await resolve(redis.client.get(key))
        assert cached is not None and "0007" in cached
        assert "fixture-variza" not in cached
        ttl = await resolve(redis.client.ttl(key))
        assert 0 < ttl <= 300
    url = f"{GATEWAYS}/{row['id']}"
    assert (await client.get(url)).json()["data"] == row

    other = await client.post(GATEWAYS, json=data | {"title": "Alternate"})
    assert other.status_code == 409, other.text

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
    assert "config" not in updated.json()["data"]

    query = {
        "kind": "variza",
        "is_active": True,
        "q": "gateway",
        "per_page": 1,
    }
    page = await client.get(GATEWAYS, params=query)
    assert page.status_code == 200, page.text
    assert [item["id"] for item in page.json()["data"]] == [row["id"]]
    assert page.json()["meta"]["total_items"] == 1

    rotated = await client.put(
        f"{url}/config",
        json={
            **config,
            "api_key": "fixture-rotated-api-key",
            "card_last_4": "random",
        },
    )
    assert rotated.status_code == 200, rotated.text
    assert "config" not in rotated.json()["data"]
    if redis is not None:
        assert await resolve(redis.client.get(key)) is None
    view = await client.get(config_url)
    assert view.status_code == 200, view.text
    assert view.json()["data"] == {
        "key": "variza",
        "card_last_4": "random",
        "expires_in": "30m",
    }
    assert "fixture-rotated-api-key" not in rotated.text
    assert (
        await client.put(f"{GATEWAYS}/9223372036854775807/config", json=config)
    ).status_code == 404

    async with container() as scope:
        repo = await scope.get(IConfigService)
        stored = await repo.find(GatewayKind.VARIZA)
    assert stored is not None
    assert pg.crypto is not None
    for field, plaintext in (
        ("api_key", "fixture-rotated-api-key"),
        ("webhook_secret", config["webhook_secret"]),
    ):
        encrypted = stored.config[field]
        assert isinstance(encrypted, str)
        assert encrypted != plaintext
        assert decrypt(encrypted, pg.crypto.encryption_key) == plaintext
