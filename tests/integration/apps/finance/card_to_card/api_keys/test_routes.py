"""Verify the Finance panel's webhook API key lifecycle."""

from datetime import timedelta
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.security.crypto import hash_sha256
from papilio.types.constants import INT64_MAX
from papilio.utils.dates import utc_now

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.finance.card_to_card.api_keys.app.interfaces.services import (
    IAPIKeyService,
)
from src.apps.finance.card_to_card.api_keys.infra.pg.repositories.crud import (
    APIKeyRepository,
)

pytestmark = pytest.mark.integration
KEYS = "/admin/card-to-card/api-keys"


async def test_api_keys(app: FastAPI, client: AsyncClient) -> None:
    now = utc_now()
    data = {
        "title": "Bank feed",
        "expires_at": (now + timedelta(days=1)).isoformat(),
    }
    assert (await client.post(KEYS, json=data)).status_code == 401
    grants: dict[str, int] = {"finance": AdminPermission.READ}

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, grants, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    try:
        assert (await client.post(KEYS, json=data)).status_code == 403
        grants["finance"] |= AdminPermission.CREATE
        expired = await client.post(
            KEYS, json=data | {"expires_at": now.isoformat()}
        )
        assert expired.status_code == 400, expired.text
        naive = await client.post(
            KEYS,
            json=data
            | {
                "expires_at": (now + timedelta(days=1))
                .replace(tzinfo=None)
                .isoformat()
            },
        )
        assert naive.status_code == 422, naive.text

        created = await client.post(KEYS, json=data)
        assert created.status_code == 201, created.text
        assert created.headers["cache-control"] == "no-store"
        issued = created.json()["data"]
        key, metadata = issued["key"], issued["api_key"]
        assert key.startswith(metadata["prefix"])
        assert metadata["title"] == data["title"]
        assert metadata["revoked_at"] is None
        assert "digest" not in metadata

        key_path = f"{KEYS}/{metadata['id']}"
        detail = await client.get(key_path)
        assert detail.status_code == 200, detail.text
        assert detail.json()["data"] == metadata
        page = await client.get(KEYS, params={"per_page": 1})
        assert page.status_code == 200, page.text
        assert page.json()["data"] == [metadata]
        assert key not in detail.text and key not in page.text

        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            repo = await scope.get(APIKeyRepository)
            record = await repo.get_by_id(metadata["id"])
            assert record is not None
            assert record.digest == hash_sha256(key)
            assert record.digest != key
            service = await scope.get(IAPIKeyService)
            assert await service.verify(key) == record.id
            assert await service.verify(key + "x") is None

        path = f"{key_path}/revoke"
        assert (await client.patch(path)).status_code == 403
        grants["finance"] |= AdminPermission.UPDATE
        revoked = await client.patch(path)
        assert revoked.status_code == 200, revoked.text
        assert revoked.json()["data"]["revoked_at"] is not None
        assert (await client.patch(path)).json()["data"] == revoked.json()[
            "data"
        ]
        assert (
            await client.patch(f"{KEYS}/{INT64_MAX}/revoke")
        ).status_code == 404
        async with container() as scope:
            service = await scope.get(IAPIKeyService)
            assert await service.verify(key) is None

        second = await client.post(KEYS, json=data | {"title": "Backup feed"})
        assert second.status_code == 201, second.text
        another = second.json()["data"]
        other_key, other_id = another["key"], another["api_key"]["id"]
        assert key != other_key
        async with container() as scope:
            service = await scope.get(IAPIKeyService)
            repo = await scope.get(APIKeyRepository)
            assert await service.verify(other_key) == other_id
            async with transaction():
                await repo.update_by_id(other_id, {"expires_at": utc_now()})
            assert await service.verify(other_key) is None
    finally:
        app.dependency_overrides.pop(current_admin, None)
