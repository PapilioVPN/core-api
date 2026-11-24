"""Exercise private receipt images through the native application."""

from io import BytesIO
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from PIL import Image

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)
from src.settings.config import CoreSettings

pytestmark = [pytest.mark.integration, pytest.mark.api]
IMAGES = "/admin/receipts/images"


@pytest.fixture
def pg(pg: CoreSettings, tmp_path: Path) -> CoreSettings:
    pg.storage.path = str(tmp_path / "media")
    pg.storage.temp_dir = str(tmp_path / "tmp")
    pg.storage.max_file_size = 1024
    return pg


async def test_receipt_image(
    app: FastAPI, client: AsyncClient, tmp_path: Path
) -> None:
    buffer = BytesIO()
    with Image.new("RGB", (4, 4)) as image:
        image.save(buffer, format="PNG")
    data = buffer.getvalue()
    params = {"format": "png"}
    response = await client.post(IMAGES, params=params, content=data)
    assert response.status_code == 401

    scopes: dict[str, int] = {}

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, scopes, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    response = await client.post(IMAGES, params=params, content=data)
    assert response.status_code == 403

    scopes["billing"] = AdminPermission.CREATE
    invalid = await client.post(IMAGES, params=params, content=b"not an image")
    assert invalid.status_code == 400
    mismatch = await client.post(
        IMAGES, params={"format": "jpeg"}, content=data
    )
    assert mismatch.status_code == 400
    oversized = await client.post(IMAGES, params=params, content=b"x" * 1025)
    assert oversized.status_code == 413

    created = await client.post(IMAGES, params=params, content=data)
    assert created.status_code == 201, created.text
    url = created.json()["data"]["url"]
    assert url.startswith(f"{IMAGES}/png/")
    again = await client.post(IMAGES, params=params, content=data)
    assert again.status_code == 201
    assert again.json()["data"]["url"] == url
    assert list((tmp_path / "media").rglob("*")) == []
    paths = list((tmp_path / "media-private").glob("*/*/*"))
    assert len(paths) == 1
    assert paths[0].read_bytes() == data
    assert (await client.get(url)).status_code == 403

    scopes["billing"] = AdminPermission.READ
    response = await client.get(url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "no-store"
    assert response.content == data

    receipt = {"image_url": url}
    response = await client.post("/admin/receipts", json=receipt)
    assert response.status_code == 403

    scopes["billing"] = AdminPermission.CREATE
    invalid_url = await client.post(
        "/admin/receipts", json={"image_url": "https://example.com/image"}
    )
    assert invalid_url.status_code == 422
    missing_image = await client.post(
        "/admin/receipts", json={"image_url": f"{IMAGES}/png/{'0' * 64}"}
    )
    assert missing_image.status_code == 404
    response = await client.post("/admin/receipts", json=receipt)
    assert response.status_code == 201, response.text
    registered = response.json()["data"]
    assert registered["id"] > 0
    assert registered["image_url"] == url
    assert registered["amount"] is None
    assert registered["paid_at"] is None
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        repo = await scope.get(ReceiptRepository)
        stored = await repo.get_by_id(registered["id"])
    assert stored is not None
    assert stored.image_url == url

    scopes["billing"] = AdminPermission.READ
    missing = await client.get(f"{IMAGES}/png/{'0' * 64}")
    assert missing.status_code == 404
    assert app.dependency_overrides.pop(current_admin) is admin
    assert (await client.get(url)).status_code == 401
