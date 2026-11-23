"""Exercise category and parameter definitions through the panel API."""

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


async def test_category_attributes(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-catalog-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="catalog-test", title="Catalog Test")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Catalog",
                last_name="Admin",
                mobile="09120000031",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )
        viewer = await users.create(
            UserCreate(
                first_name="Catalog",
                last_name="Viewer",
                mobile="09120000032",
                role_id=role.id,
                password=password,
            )
        )

    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.is_success, login.text
    token = login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    categories = "/admin/categories"
    attributes = "/admin/attributes"
    assert (await client.get(categories)).status_code == 401
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": viewer.mobile, "password": password},
    )
    assert login.is_success, login.text
    token = login.json()["data"]["access_token"]
    forbidden = await client.get(
        categories, headers={"Authorization": f"Bearer {token}"}
    )
    assert forbidden.status_code == 403

    category = await client.post(
        categories,
        headers=headers,
        json={"slug": "catalog-test", "title": "Catalog Test"},
    )
    assert category.status_code == 201, category.text
    category_id = category.json()["data"]["id"]

    data = {"key": "test_quota", "label": "Quota", "type": "str"}
    invalid = await client.post(
        attributes,
        headers=headers,
        json={**data, "param_key": "quota_bytes"},
    )
    assert invalid.status_code == 400, invalid.text
    assert invalid.json()["error"]["message_code"] == "invalid_param_type"
    attribute = await client.post(
        attributes, headers=headers, json={**data, "type": "int"}
    )
    assert attribute.status_code == 201, attribute.text
    attribute_id = attribute.json()["data"]["id"]

    attribute = await client.patch(
        f"{attributes}/{attribute_id}",
        headers=headers,
        json={"param_key": "duration_days"},
    )
    assert attribute.is_success, attribute.text
    assert attribute.json()["data"]["param_key"] == "duration_days"
    bindings = f"{categories}/{category_id}/attributes"
    binding = f"{bindings}/{attribute_id}"
    missing = await client.put(f"{bindings}/99999", headers=headers, json={})
    assert missing.status_code == 404, missing.text
    for _ in range(2):
        saved = await client.put(
            binding, headers=headers, json={"is_required": True}
        )
        assert saved.is_success, saved.text
    listed = await client.get(bindings, headers=headers)
    assert listed.is_success, listed.text
    entries = listed.json()["data"]
    assert len(entries) == 1
    assert entries[0]["is_required"] is True
    assert entries[0]["attribute"]["param_key"] == "duration_days"

    removed = await client.delete(binding, headers=headers)
    assert removed.is_success, removed.text
    listed = await client.get(bindings, headers=headers)
    assert listed.json()["data"] == []
    attribute = await client.get(
        f"{attributes}/{attribute_id}", headers=headers
    )
    assert attribute.is_success, attribute.text
    cleared = await client.patch(
        f"{attributes}/{attribute_id}",
        headers=headers,
        json={"param_key": None},
    )
    assert cleared.is_success, cleared.text
    assert cleared.json()["data"]["param_key"] is None
