"""Exercise catalog setup, reusable terms, and panel search."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.roles.app.interfaces.services import IRoleService
from src.apps.core.roles.domain.dtos.records import RoleCreate
from src.apps.core.users.app.interfaces.commands import IUserCreateCommand
from src.apps.core.users.domain.dtos.records import UserCreate

pytestmark = pytest.mark.integration


async def test_catalogs(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-shop-catalogs-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="catalog-admin", title="Catalog Admin")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Catalog",
                last_name="Admin",
                mobile="09120000045",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }
    url = "/admin/catalogs"
    assert (await client.get(url)).status_code == 401

    created = await client.post(
        "/admin/services", json={"title": "Catalog VPN"}, headers=headers
    )
    assert created.status_code == 201, created.text
    service = created.json()["data"]
    custom = {
        "mode": "custom",
        "min_bytes": 10 * 1024**3,
        "max_bytes": 50 * 1024**3,
        "step_bytes": 10 * 1024**3,
    }
    body = {"title": "Starter", "service_id": service["id"], "price": 10000}
    form = await client.get(f"{url}/form", headers=headers)
    assert form.status_code == 200, form.text
    form_data = form.json()["data"]
    assert service in form_data["services"]["items"]
    assert form_data["min_price"] == 10000 and form_data["currency"] == "IRR"
    invalid = await client.post(
        url, json={**body, "volume": custom}, headers=headers
    )
    assert invalid.status_code == 422, invalid.text

    low = await client.post(url, json={**body, "price": 9999}, headers=headers)
    assert low.status_code == 422, low.text
    created = await client.post(url, json=body, headers=headers)
    assert created.status_code == 201, created.text
    first = created.json()["data"]
    assert first["volume_id"] is None and first["duration_id"] is None
    path = f"{url}/{first['id']}"
    low = await client.patch(path, json={"price": 9999}, headers=headers)
    assert low.status_code == 422, low.text

    volume = {"size_bytes": 30 * 1024**3}
    duration = {"days": 60}
    updated = await client.patch(
        path, json={"volume": volume, "duration": duration}, headers=headers
    )
    assert updated.status_code == 200, updated.text
    first = updated.json()["data"]
    assert first["volume_id"] and first["duration_id"]

    upper_price = 2**63 - 1
    created = await client.post(
        url,
        json={
            **body,
            "title": "Starter Plus",
            "price": upper_price,
            "status": "published",
            "volume": volume,
            "duration": first["duration_id"],
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    second = created.json()["data"]
    assert second["price"] == upper_price
    assert second["volume_id"] == first["volume_id"]
    assert second["duration_id"] == first["duration_id"]

    bad = await client.patch(
        path,
        json={
            "volume": {"size_bytes": 37 * 1024**3},
            "duration": 99999,
        },
        headers=headers,
    )
    assert bad.status_code == 404, bad.text
    volumes = await client.get(
        "/admin/volumes",
        params={"size_bytes": 37 * 1024**3},
        headers=headers,
    )
    assert volumes.json()["data"] == []
    detail = await client.get(path, headers=headers)
    assert detail.status_code == 200, detail.text
    result = detail.json()["data"]
    assert result["catalog"] == first
    assert result["volume"]["size_bytes"] == volume["size_bytes"]
    assert result["duration"]["days"] == 60

    listed = await client.get(
        url,
        params={
            "q": "Catalog VPN",
            "status": "published",
            "min_price": upper_price,
        },
        headers=headers,
    )
    assert listed.status_code == 200, listed.text
    page = listed.json()
    assert page["data"] == [second]
    assert page["meta"]["pager"]["total_items"] == 1
    status = next(
        item for item in page["meta"]["filters"] if item["key"] == "status"
    )
    assert {item["id"]: item["count"] for item in status["options"]} == {
        "draft": 1,
        "published": 1,
    }

    changed = await client.patch(path, json={"volume": None}, headers=headers)
    assert changed.status_code == 200, changed.text
    assert changed.json()["data"]["volume_id"] is None
    assert changed.json()["data"]["duration_id"] == first["duration_id"]
    detail = await client.get(path, headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["volume"] is None
