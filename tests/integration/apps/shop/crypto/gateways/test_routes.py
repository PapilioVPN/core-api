"""Manage crypto gateways through the Shop administrator API."""

from decimal import Decimal
from secrets import randbelow
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
    data = {
        "key": f"account-{suffix}",
        "title": "Example Gateway",
        "kind": "example-provider",
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
    assert record["kind"] == "example-provider"
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
    for q, count in (("example", 1), ("%%", 0)):
        page = await client.get(
            path,
            headers=headers,
            params={"q": q, "kind": "example-provider", "is_active": True},
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
    removed = await client.delete(detail, headers=headers)
    assert removed.is_success, removed.text
    assert removed.json()["data"]["id"] == record["id"]
    assert (await client.get(detail, headers=headers)).status_code == 404
