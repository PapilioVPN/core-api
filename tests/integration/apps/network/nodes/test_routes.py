"""Register and manage independent nodes through the administrator API."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate

pytestmark = pytest.mark.integration

PASSWORD = "isolated-network-nodes-password"
NODES = "/admin/nodes"


async def login(client: AsyncClient, mobile: str) -> dict[str, str]:
    response = await client.post(
        "/admin/auth/tokens", json={"mobile": mobile, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {
        "Authorization": f"Bearer {response.json()['data']['access_token']}"
    }


async def test_nodes(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="network-operator", title="Network Operator")
        )
        users = await scope.get(IUserCreateCommand)
        owner = await users.create(
            UserCreate(
                first_name="Network",
                last_name="Owner",
                mobile="09120000814",
                role_id=role.id,
                password=PASSWORD,
            ),
            super_admin=True,
        )
        operator = await users.create(
            UserCreate(
                first_name="Network",
                last_name="Operator",
                mobile="09120000815",
                role_id=role.id,
                password=PASSWORD,
            )
        )

    assert (await client.get(NODES)).status_code == 401
    headers = await login(client, owner.mobile)
    operator_headers = await login(client, operator.mobile)
    assert (
        await client.get(NODES, headers=operator_headers)
    ).status_code == 403

    endpoint = {
        "name": "Registry East",
        "address": "EAST.Example.invalid",
        "port": 8443,
    }
    created = await client.post(NODES, headers=headers, json=endpoint)
    assert created.status_code == 201, created.text
    east = created.json()["data"]
    assert east["address"] == "east.example.invalid"
    assert east["is_enabled"] is True
    assert east["connection_status"] == "unchecked"
    assert east["last_checked_at"] is None
    assert east["last_seen_at"] is None
    assert east["connection_stale"] is False
    path = f"{NODES}/{east['id']}"

    other_endpoint = {
        "name": "Registry West",
        "address": "2001:db8::1",
        "port": 9443,
        "is_enabled": False,
    }
    created = await client.post(NODES, headers=headers, json=other_endpoint)
    assert created.status_code == 201, created.text
    west = created.json()["data"]
    assert west["id"] != east["id"]
    assert west["is_enabled"] is False
    assert west["connection_status"] == "unchecked"

    scope_response = await client.post(
        "/admin/scopes",
        headers=headers,
        json={"key": "network", "title": "Network"},
    )
    assert scope_response.status_code == 201, scope_response.text
    grant = await client.post(
        f"/admin/roles/{role.id}/scopes/batch",
        headers=headers,
        json={
            "items": [
                {
                    "scope_id": scope_response.json()["data"]["id"],
                    "permissions": AdminPermission.READ,
                }
            ]
        },
    )
    assert grant.status_code == 200, grant.text
    assert (await client.get(path, headers=operator_headers)).json()[
        "data"
    ] == east
    live = await client.get(f"{path}/host-stats", headers=operator_headers)
    assert live.status_code == 200, live.text
    assert live.json()["data"] == {
        "node_id": east["id"],
        "status": "not_configured",
        "stats": None,
        "received_at": None,
    }
    assert (
        await client.post(NODES, headers=operator_headers, json=endpoint)
    ).status_code == 403
    assert (
        await client.patch(
            path, headers=operator_headers, json={"is_enabled": False}
        )
    ).status_code == 403

    page = await client.get(
        NODES,
        headers=operator_headers,
        params={"per_page": 1, "q": "Registry"},
    )
    assert page.status_code == 200, page.text
    assert page.json()["data"] == [west]
    assert page.json()["meta"]["total_items"] == 2

    duplicate = await client.post(NODES, headers=headers, json=endpoint)
    assert duplicate.status_code == 409, duplicate.text
    duplicate_patch = await client.patch(
        path, headers=headers, json={"address": "2001:0db8::1", "port": 9443}
    )
    assert duplicate_patch.status_code == 409, duplicate_patch.text
    assert (await client.get(path, headers=headers)).json()["data"] == east

    paused = await client.patch(
        path, headers=headers, json={"is_enabled": False}
    )
    assert paused.status_code == 200, paused.text
    row = paused.json()["data"]
    assert {key: row[key] for key in endpoint} == {
        **endpoint,
        "address": "east.example.invalid",
    }
    assert row["is_enabled"] is False
    assert row["connection_status"] == "unchecked"

    filtered = await client.get(
        NODES,
        headers=operator_headers,
        params={"q": "EAST", "is_enabled": False},
    )
    assert filtered.status_code == 200, filtered.text
    assert filtered.json()["data"] == [row]

    empty = await client.patch(path, headers=headers, json={})
    assert empty.status_code == 400, empty.text
    assert empty.json()["error"]["message_code"] == "empty_input"
    for data in (
        {"name": None},
        {"address": "https://example.invalid"},
        {"port": 0},
    ):
        invalid = await client.patch(path, headers=headers, json=data)
        assert invalid.status_code == 422, invalid.text
    assert (
        await client.get(f"{NODES}/99999", headers=headers)
    ).status_code == 404
    missing = await client.patch(
        f"{NODES}/99999", headers=headers, json={"name": "Absent"}
    )
    assert missing.status_code == 404, missing.text
