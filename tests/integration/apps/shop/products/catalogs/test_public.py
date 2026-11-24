"""Verify visibility at the public storefront entrypoints."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate

pytestmark = pytest.mark.integration


async def test_public(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-shop-public-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="storefront-admin", title="Storefront Admin")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Storefront",
                last_name="Admin",
                mobile="09120000047",
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

    service = await client.post(
        "/admin/services",
        json={"title": "Storefront Premium"},
        headers=headers,
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["data"]["id"]
    offers = f"/public/services/{service_id}/catalogs"

    empty = await client.get(offers)
    assert empty.status_code == 200, empty.text
    assert empty.json()["data"] == []
    assert empty.json()["meta"]["total_items"] == 0
    assert (
        await client.get("/public/services/99999999/catalogs")
    ).status_code == 404

    services = await client.get("/public/services", params={"q": "Storefront"})
    assert services.status_code == 200, services.text
    assert services.json()["data"] == [
        {"id": service_id, "title": "Storefront Premium", "description": None}
    ]
    past_services = await client.get(
        "/public/services", params={"q": "Storefront", "page": 2**63}
    )
    assert past_services.status_code == 200, past_services.text
    assert past_services.json()["data"] == []
    assert past_services.json()["meta"]["total_items"] == 1

    other = await client.post(
        "/admin/services",
        json={"title": "Storefront Economy"},
        headers=headers,
    )
    assert other.status_code == 201, other.text
    other_id = other.json()["data"]["id"]
    created = {}
    for key, extra in (
        ("draft", {}),
        ("paused", {"status": "paused"}),
        ("unlimited", {"status": "published", "priority": 20}),
        (
            "fixed",
            {
                "status": "published",
                "priority": 10,
                "volume": {"size_bytes": 32212254720},
                "duration": {"days": 14},
            },
        ),
        ("other", {"service_id": other_id, "status": "published"}),
    ):
        response = await client.post(
            "/admin/catalogs",
            json={
                "service_id": service_id,
                "title": f"Storefront {key}",
                "price": 10000,
                **extra,
            },
            headers=headers,
        )
        assert response.status_code == 201, response.text
        created[key] = response.json()["data"]["id"]

    first = await client.get(offers, params={"per_page": 1})
    assert first.status_code == 200, first.text
    assert first.json()["meta"]["total_items"] == 2
    fixed = first.json()["data"][0]
    assert fixed["id"] == created["fixed"]
    assert fixed["service_id"] == service_id
    assert fixed["price"] == 10000
    assert fixed["volume_bytes"] == 32212254720
    assert fixed["duration_days"] == 14 and fixed["starts_on"] == "ready"
    assert "status" not in fixed and "created_at" not in fixed
    second = await client.get(offers, params={"per_page": 1, "page": 2})
    assert second.status_code == 200, second.text
    unlimited = second.json()["data"][0]
    assert unlimited["id"] == created["unlimited"]
    assert unlimited["volume_bytes"] is None
    assert (
        unlimited["duration_days"] is None and unlimited["starts_on"] is None
    )
    past_end = await client.get(offers, params={"per_page": 1, "page": 3})
    assert past_end.json()["data"] == []
    assert past_end.json()["meta"]["total_items"] == 2

    searched = await client.get(
        offers,
        params={"q": "FIXED", "is_unlimited": False, "has_expiry": True},
    )
    assert searched.status_code == 200, searched.text
    assert searched.json()["data"] == [fixed]
    assert searched.json()["meta"]["total_items"] == 1
    unlimited_only = await client.get(
        offers, params={"is_unlimited": True, "has_expiry": False}
    )
    assert unlimited_only.status_code == 200, unlimited_only.text
    assert unlimited_only.json()["data"] == [unlimited]
    escaped = await client.get(offers, params={"q": "%"})
    assert escaped.status_code == 200, escaped.text
    assert escaped.json()["data"] == []

    url = "/public/catalogs"
    assert (await client.get(url)).status_code == 404
    path = f"{url}/{created['fixed']}"
    detail = await client.get(path)
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"] == fixed
    for status in ("draft", "paused"):
        hidden = await client.get(f"{url}/{created[status]}")
        assert hidden.status_code == 404, hidden.text

    stopped = await client.patch(
        f"/admin/catalogs/{created['fixed']}",
        json={"status": "paused"},
        headers=headers,
    )
    assert stopped.status_code == 200, stopped.text
    assert (await client.get(path)).status_code == 404
    page = await client.get(offers)
    assert page.json()["data"] == [unlimited]

    updated = await client.patch(
        f"/admin/services/{service_id}",
        json={"is_active": False},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert (await client.get(offers)).status_code == 404
    assert (
        await client.get(f"{url}/{created['unlimited']}")
    ).status_code == 404
    assert (await client.get(f"{url}/{created['other']}")).status_code == 200
    services = await client.get("/public/services", params={"q": "Storefront"})
    assert services.status_code == 200, services.text
    assert [item["id"] for item in services.json()["data"]] == [other_id]
