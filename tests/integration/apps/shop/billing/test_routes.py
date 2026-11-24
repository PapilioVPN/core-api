"""Upload receipt evidence and register payments through the admin API."""

from collections.abc import AsyncIterator
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from PIL import Image
from pydantic import HttpUrl

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.configs.infra.pg.repositories.storage import (
    StorageConfigRepository,
)
from src.apps.shop.billing.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)
from src.apps.shop.billing.receipts.infra.pg.repositories.crud import (
    ReceiptRepository,
)
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration
MEDIA_URL = "https://media.example.org/receipts/"


@pytest.fixture
def pg(pg: CoreSettings, tmp_path: Path) -> CoreSettings:
    pg.storage.path = str(tmp_path / "media")
    pg.storage.temp_dir = str(tmp_path / "staging")
    pg.storage.public_base_url = HttpUrl(MEDIA_URL)
    pg.storage.max_file_size = 1024
    return pg


@pytest.fixture
async def local_storage(
    app: FastAPI, client: AsyncClient
) -> AsyncIterator[None]:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        configs = await scope.get(StorageConfigRepository)
        async with transaction():
            previous = await configs.get_backend()
            selected = await configs.save(StorageBackend.LOCAL)
    try:
        yield
    finally:
        async with container() as scope:
            configs = await scope.get(StorageConfigRepository)
            async with transaction():
                if previous is None:
                    await configs.remove_by_id(selected.id)
                else:
                    await configs.save(previous)


@pytest.mark.usefixtures("local_storage")
async def test_post_payment(
    app: FastAPI, client: AsyncClient, tmp_path: Path
) -> None:
    path = "/admin/payments"
    images = "/admin/receipts/images"
    params = {"original_name": "receipt.png", "mime_type": "image/png"}
    data = {"amount": 4_000_000_005, "image_url": "/media/receipt.png"}
    assert (await client.post(path, json=data)).status_code == 401
    assert (
        await client.post(images, params=params, content=b"")
    ).status_code == 401

    password = "isolated-billing-operator-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(RoleCreate(key="billing", title="Billing"))
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Billing",
                last_name="Admin",
                mobile="09120000081",
                password=password,
                role_id=role.id,
            ),
            super_admin=True,
        )
        viewer = await users.create(
            UserCreate(
                first_name="Billing",
                last_name="Viewer",
                mobile="09120000082",
                password=password,
                role_id=role.id,
            )
        )

    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": viewer.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }
    assert (
        await client.post(path, json=data, headers=headers)
    ).status_code == 403
    assert (
        await client.post(images, params=params, content=b"", headers=headers)
    ).status_code == 403

    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }

    invalid_image = await client.post(
        images, params=params, content=b"not a PNG", headers=headers
    )
    assert invalid_image.status_code == 400, invalid_image.text
    too_large = await client.post(
        images, params=params, content=bytes(1025), headers=headers
    )
    assert too_large.status_code == 413
    assert not list((tmp_path / "media").rglob("*"))

    with Image.new("RGB", (2, 2), (60, 120, 10)) as image, BytesIO() as source:
        image.save(source, format="PNG")
        payload = source.getvalue()
    mismatch = await client.post(
        images,
        params={**params, "mime_type": "image/jpeg"},
        content=payload,
        headers=headers,
    )
    assert mismatch.status_code == 400, mismatch.text
    uploaded = await client.post(
        images, params=params, content=payload, headers=headers
    )
    assert uploaded.status_code == 201, uploaded.text
    digest = sha256(payload).hexdigest()
    key = f"{digest[:2]}/{digest}"
    assert uploaded.json()["data"] == {"url": f"{MEDIA_URL}{key}"}
    assert (tmp_path / "media" / key).read_bytes() == payload
    assert not list((tmp_path / "staging").iterdir())
    data["image_url"] = uploaded.json()["data"]["url"]

    invalid = await client.post(
        path, json={**data, "amount": 0}, headers=headers
    )
    assert invalid.status_code == 422
    invalid = await client.post(
        path,
        json={**data, "image_url": "file:///receipt.jpg"},
        headers=headers,
    )
    assert invalid.status_code == 422

    created = await client.post(path, json=data, headers=headers)
    assert created.status_code == 201, created.text
    payment = created.json()["data"]
    assert payment["amount"] == data["amount"]
    assert payment["status"] == "pending"
    assert payment["confirmed_at"] is None
    assert payment["created_at"] and payment["updated_at"]

    async with container() as scope:
        payments = await scope.get(PaymentRepository)
        receipts = await scope.get(ReceiptRepository)
        try:
            stored = await payments.get_by_id(payment["id"])
            assert (
                stored is not None
                and stored.receipt_id == payment["receipt_id"]
            )
            receipt = await receipts.get_by_id(stored.receipt_id)
            assert (
                receipt is not None and receipt.image_url == data["image_url"]
            )
        finally:
            async with transaction():
                await payments.remove_by_id(payment["id"])
                await receipts.remove_by_id(payment["receipt_id"])
