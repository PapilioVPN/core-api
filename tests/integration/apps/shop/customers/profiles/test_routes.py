"""Read, edit and filter customers in the administrator panel."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.access.roles.domain.dtos.role_scopes import RoleScopeCreate
from src.apps.core.access.scopes.app.interfaces.services import IScopeService
from src.apps.core.access.scopes.domain.dtos.records import ScopeCreate

pytestmark = pytest.mark.integration
URL = "/admin/customers"


@pytest.mark.parametrize("admin", [("072", True)], indirect=True)
async def test_profiles(client: AsyncClient, admin: dict[str, str]) -> None:
    assert (await client.get(URL)).status_code == 401
    invalid = await client.post(
        URL, headers=admin, json={"name": "Invalid", "mobile": "bad-mobile"}
    )
    assert invalid.status_code == 422
    created = await client.post(
        URL,
        headers=admin,
        json={
            "name": "مشتری آزمایشی",
            "mobile": "09120000077",
            "note": "Panel note",
            "group_id": 99999,
        },
    )
    assert created.status_code == 201
    customer = created.json()["data"]
    assert customer["group_id"] is None
    assert customer["is_blocked"] is False
    path = f"{URL}/{customer['id']}"
    assert (await client.get(path, headers=admin)).json()["data"] == customer

    created = await client.post(URL, headers=admin, json={"name": "No Mobile"})
    assert created.status_code == 201
    assert created.json()["data"]["mobile"] is None
    rows = await client.get(
        URL, headers=admin, params={"q": "000077", "is_blocked": False}
    )
    assert rows.json()["data"] == [customer]
    assert rows.json()["meta"]["total_items"] == 1
    literal = await client.get(URL, headers=admin, params={"q": "%"})
    assert literal.json()["data"] == []
    batch = await client.get(
        f"{URL}/batch",
        headers=admin,
        params={"ids": [customer["id"], customer["id"], 99999]},
    )
    assert batch.json()["data"] == [customer]

    blocked = await client.patch(
        path, headers=admin, json={"is_blocked": True, "note": None}
    )
    blocked = blocked.json()["data"]
    assert blocked["is_blocked"] is True
    assert blocked["note"] is None
    assert blocked["mobile"] == customer["mobile"]
    rows = await client.get(
        URL, headers=admin, params={"q": "آزمایشی", "is_blocked": True}
    )
    assert rows.json()["data"] == [blocked]
    unblocked = await client.patch(
        path, headers=admin, json={"is_blocked": False, "mobile": None}
    )
    assert unblocked.json()["data"]["is_blocked"] is False
    assert unblocked.json()["data"]["mobile"] is None
    assert (
        await client.patch(path, headers=admin, json={"name": None})
    ).status_code == 422
    assert (await client.get(f"{URL}/99999", headers=admin)).status_code == 404


@pytest.mark.parametrize("admin", [("073", False)], indirect=True)
async def test_profiles_require_customer_scope(
    app: FastAPI, client: AsyncClient, admin: dict[str, str]
) -> None:
    assert (await client.get(URL, headers=admin)).status_code == 403
    assert (
        await client.get("/admin/customer-groups", headers=admin)
    ).status_code == 403

    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.find_by_key("customer-test-073")
        assert role is not None
        scopes = await scope.get(IScopeService)
        customers = await scopes.create(
            ScopeCreate(key="customers", title="Customers")
        )
        grants = await scope.get(IRoleScopeService)
        await grants.create(
            role.id,
            RoleScopeCreate(
                scope_id=customers.id, permissions=AdminPermission.READ
            ),
        )
    assert (await client.get(URL, headers=admin)).status_code == 200
    assert (
        await client.get("/admin/customer-groups", headers=admin)
    ).status_code == 200
    assert (
        await client.post(URL, headers=admin, json={"name": "Forbidden"})
    ).status_code == 403
