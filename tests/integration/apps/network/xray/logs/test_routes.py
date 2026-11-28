"""Exercise live-log authorization and absent targets at the Panel."""

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

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


async def test_log_stream_requires_authentication(client: AsyncClient) -> None:
    reply = await client.get("/admin/nodes/1/xray/instances/edge/logs")
    assert reply.status_code == 401, reply.text


async def test_log_stream_requires_read_grant(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-xray-logs-operator-password"
    mobile = "09120000777"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="xray-logs-ungranted", title="No Logs Grant")
        )
        users = await scope.get(IUserCreateCommand)
        await users.create(
            UserCreate(
                first_name="Logs",
                last_name="Operator",
                mobile=mobile,
                role_id=role.id,
                password=password,
            )
        )
    login = await client.post(
        "/admin/auth/tokens", json={"mobile": mobile, "password": password}
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    reply = await client.get(
        "/admin/nodes/1/xray/instances/edge/logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reply.status_code == 403, reply.text


async def test_log_stream_reports_unconfigured_node(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000776", role_key="xray-logs"
    )
    node = await client.post(
        "/admin/nodes",
        headers=headers,
        json={"name": "Log fixture", "address": "logs.invalid", "port": 81},
    )
    assert node.status_code == 201, node.text
    id = node.json()["data"]["id"]
    reply = await client.get(
        f"/admin/nodes/{id}/xray/instances/edge/logs", headers=headers
    )
    assert reply.status_code == 200, reply.text
    assert reply.headers["content-type"].startswith("text/event-stream")
    assert "no-store" in reply.headers["cache-control"]
    assert "event: end" in reply.text
    assert '"status":"not_configured"' in reply.text
