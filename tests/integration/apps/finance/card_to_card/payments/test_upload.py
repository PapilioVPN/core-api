"""Verify receipt upload uses Storage without creating a payment."""

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from PIL import Image
from pydantic import HttpUrl

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.configs.infra.pg.repositories.storage import (
    StorageConfigRepository,
)
from src.apps.finance.card_to_card.payments.infra.pg.repositories.crud import (
    CardPaymentRepository,
)
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration
RECEIPTS = "/admin/card-payments/receipts"
MEDIA_URL = "https://media.example.org/finance/"


@pytest.fixture
def pg(pg: CoreSettings, tmp_path: Path) -> CoreSettings:
    pg.storage.path = str(tmp_path / "media")
    pg.storage.temp_dir = str(tmp_path / "staging")
    pg.storage.public_base_url = HttpUrl(MEDIA_URL)
    pg.storage.max_file_size = 1024
    return pg


async def test_receipt_upload(
    app: FastAPI, client: AsyncClient, tmp_path: Path
) -> None:
    params = {"original_name": "receipt.png", "mime_type": "image/png"}
    assert (await client.post(RECEIPTS, params=params)).status_code == 401

    scopes: dict[str, int] = {
        "finance": AdminPermission.READ,
        "storage": AdminPermission.CREATE,
    }

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, scopes, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    assert (await client.post(RECEIPTS, params=params)).status_code == 403
    scopes["finance"] |= AdminPermission.CREATE
    del scopes["storage"]

    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        configs = await scope.get(StorageConfigRepository)
        payments = await scope.get(CardPaymentRepository)
        count = await payments.count()
        async with transaction():
            previous = await configs.get_backend()
            selected = await configs.save(StorageBackend.LOCAL)

    try:
        with (
            Image.new("RGB", (2, 2), (33, 81, 17)) as image,
            BytesIO() as file,
        ):
            image.save(file, format="PNG")
            payload = file.getvalue()

        wrong_mime = await client.post(
            RECEIPTS,
            params={**params, "mime_type": "image/jpeg"},
            content=payload,
        )
        assert wrong_mime.status_code == 400, wrong_mime.text
        assert (
            wrong_mime.json()["error"]["message_code"]
            == "receipt_image_invalid"
        )
        assert (
            await client.post(
                RECEIPTS,
                params={**params, "mime_type": "image/gif"},
                content=payload,
            )
        ).status_code == 422
        assert (
            await client.post(RECEIPTS, params=params, content=b"not an image")
        ).status_code == 400
        assert (
            await client.post(RECEIPTS, params=params, content=bytes(1025))
        ).status_code == 413
        assert not list((tmp_path / "media").rglob("*"))

        response = await client.post(RECEIPTS, params=params, content=payload)
        assert response.status_code == 201, response.text
        digest = sha256(payload).hexdigest()
        key = f"{digest[:2]}/{digest}"
        assert response.json()["data"] == {"url": f"{MEDIA_URL}{key}"}
        assert (tmp_path / "media" / key).read_bytes() == payload
        assert not list((tmp_path / "staging").iterdir())
        async with container() as scope:
            payments = await scope.get(CardPaymentRepository)
            assert await payments.count() == count
    finally:
        app.dependency_overrides.pop(current_admin, None)
        async with container() as scope:
            configs = await scope.get(StorageConfigRepository)
            async with transaction():
                if previous is None:
                    await configs.remove_by_id(selected.id)
                else:
                    await configs.save(previous)
