"""Verify access and native injection for the system information router."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)

pytestmark = pytest.mark.integration


async def test_runtime_info(app: FastAPI, client: AsyncClient) -> None:
    path = "/admin/health/resources/runtime"
    assert (await client.get(path)).status_code == 401

    scopes: dict[str, int] = {}

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, scopes, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    assert (await client.get(path)).status_code == 403

    scopes["system"] = AdminPermission.READ
    response = await client.get(path)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["duration_ms"] >= 0
    assert data["value"]["python_version"]
    assert data["value"]["process_id"] > 0
