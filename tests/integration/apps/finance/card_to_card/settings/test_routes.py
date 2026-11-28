"""Verify lazy creation, updates and caching of the card transfer policy."""

from asyncio import gather
from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.infra.redis.client import RedisClient, resolve

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.finance.card_to_card.settings.app.interfaces.cache import (
    ITransferSettingsCache,
)
from src.apps.finance.card_to_card.settings.app.interfaces.queries import (
    ITransferSettingsQuery,
)
from src.apps.finance.card_to_card.settings.domain.enums.records import (
    SettingsKey,
)
from src.apps.finance.card_to_card.settings.infra.pg.repositories.crud import (
    TransferSettingsRepository,
)
from src.apps.finance.card_to_card.settings.infra.redis.repositories import (
    records as cache_records,
)
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration
SETTINGS = "/admin/card-to-card/settings"
DEFAULT = {"auto_confirm": False, "digits": 4, "window_minutes": None}


@pytest.fixture
async def settings_db(
    app: FastAPI, client: AsyncClient
) -> AsyncIterator[AsyncContainer]:
    container = cast(AsyncContainer, app.state.dishka_container)
    yield container
    async with container() as scope:
        repo = await scope.get(TransferSettingsRepository)
        async with transaction():
            settings = await repo.find_by_key(SettingsKey.GENERAL)
            if settings is not None:
                await repo.remove_by_id(settings.id)
    cache = await container.get(ITransferSettingsCache)
    await cache.forget(SettingsKey.GENERAL)


async def test_transfer_settings(
    app: FastAPI, client: AsyncClient, settings_db: AsyncContainer
) -> None:
    assert (await client.get(SETTINGS)).status_code == 401

    grants: dict[str, int] = {"shop": AdminPermission.READ}

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, grants, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    enabled = {"auto_confirm": True, "digits": 5, "window_minutes": 75}
    try:
        assert (await client.get(SETTINGS)).status_code == 403
        grants["finance"] = AdminPermission.READ

        initial = await client.get(SETTINGS)
        assert initial.status_code == 200, initial.text
        assert initial.json()["data"] == DEFAULT
        assert (await client.put(SETTINGS, json=enabled)).status_code == 403
        grants["finance"] |= AdminPermission.UPDATE

        for invalid in (
            {"digits": 2},
            {"digits": 6},
            {"digits": "4"},
            {"auto_confirm": "true"},
            {"window_minutes": 0},
            {"window_minutes": 2**31},
        ):
            response = await client.put(SETTINGS, json=enabled | invalid)
            assert response.status_code == 422, response.text
        missing_window = await client.put(
            SETTINGS, json=enabled | {"window_minutes": None}
        )
        assert missing_window.status_code == 400, missing_window.text
        assert (await client.get(SETTINGS)).json()["data"] == DEFAULT
        async with settings_db() as scope:
            repo = await scope.get(TransferSettingsRepository)
            assert await repo.count() == 0

        responses = await gather(
            client.put(SETTINGS, json=enabled),
            client.put(SETTINGS, json=enabled),
        )
        for saved in responses:
            assert saved.status_code == 200, saved.text
            assert saved.json()["data"] == enabled
        assert (await client.get(SETTINGS)).json()["data"] == enabled
        async with settings_db() as scope:
            repo = await scope.get(TransferSettingsRepository)
            first = await repo.get_one()
            assert first is not None
            assert first.key is SettingsKey.GENERAL
            assert first.key.value == "general"

        disabled = await client.put(SETTINGS, json=DEFAULT)
        assert disabled.status_code == 200, disabled.text
        assert (await client.get(SETTINGS)).json()["data"] == DEFAULT
        async with settings_db() as scope:
            repo = await scope.get(TransferSettingsRepository)
            current = await repo.get_one()
            assert current is not None
            assert (current.key, current.id) == (first.key, first.id)
    finally:
        app.dependency_overrides.pop(current_admin, None)


async def test_patch_transfer_settings(
    app: FastAPI, client: AsyncClient, settings_db: AsyncContainer
) -> None:
    assert (
        await client.patch(SETTINGS, json={"digits": 5})
    ).status_code == 401

    grants: dict[str, int] = {"finance": AdminPermission.READ}

    async def admin() -> AdminIdentity:
        return AdminIdentity(1, 1, grants, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    try:
        assert (
            await client.patch(SETTINGS, json={"digits": 5})
        ).status_code == 403
        grants["finance"] |= AdminPermission.UPDATE

        for patch in ({}, {"unknown": True}, {"auto_confirm": True}):
            response = await client.patch(SETTINGS, json=patch)
            assert response.status_code == 400, response.text
        for patch in ({"digits": None}, {"auto_confirm": None}):
            response = await client.patch(SETTINGS, json=patch)
            assert response.status_code == 422, response.text
        async with settings_db() as scope:
            repo = await scope.get(TransferSettingsRepository)
            assert await repo.find_by_key(SettingsKey.GENERAL) is None

        responses = await gather(
            client.patch(SETTINGS, json={"digits": 5}),
            client.patch(SETTINGS, json={"window_minutes": 75}),
        )
        for response in responses:
            assert response.status_code == 200, response.text
        expected = DEFAULT | {"digits": 5, "window_minutes": 75}
        assert (await client.get(SETTINGS)).json()["data"] == expected

        enabled = await client.patch(SETTINGS, json={"auto_confirm": True})
        assert enabled.status_code == 200, enabled.text
        assert enabled.json()["data"] == expected | {"auto_confirm": True}

        rejected = await client.patch(SETTINGS, json={"window_minutes": None})
        assert rejected.status_code == 400, rejected.text
        assert (await client.get(SETTINGS)).json()["data"] == enabled.json()[
            "data"
        ]

        cleared = await client.patch(
            SETTINGS, json={"auto_confirm": False, "window_minutes": None}
        )
        assert cleared.status_code == 200, cleared.text
        assert cleared.json()["data"] == DEFAULT | {"digits": 5}
    finally:
        app.dependency_overrides.pop(current_admin, None)


async def test_transfer_settings_cache(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    settings_db: AsyncContainer,
) -> None:
    if pg.redis is None:
        pytest.skip("Set PAPILIOVPN_TEST_REDIS_URL to isolated Redis")

    async def admin() -> AdminIdentity:
        grants = {
            "finance": int(AdminPermission.READ | AdminPermission.UPDATE)
        }
        return AdminIdentity(1, 1, grants, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    cache = await settings_db.get(ITransferSettingsCache)
    redis = await settings_db.get(RedisClient)
    try:
        key = SettingsKey.GENERAL
        await cache.forget(key)
        assert (await client.get(SETTINGS)).status_code == 200
        assert await cache.find(key) is None
        assert (await client.put(SETTINGS, json=DEFAULT)).status_code == 200
        assert (await client.get(SETTINGS)).status_code == 200
        cached = await cache.find(key)
        assert cached is not None
        assert cached.key is key
        prefix = cache_records.TransferSettingsCache.prefix
        ttl = await resolve(redis.client.ttl(f"{prefix}:{key}"))
        assert 0 < ttl <= 300

        async with settings_db() as scope:
            repo = await scope.get(TransferSettingsRepository)
            query = await scope.get(ITransferSettingsQuery)
            async with transaction():
                await repo.update_by_id(cached.id, {"digits": 3})
                assert (await query.get(key)).digits == 3
                assert await cache.find(key) == cached
                await repo.update_by_id(cached.id, {"digits": cached.digits})

        rejected = await client.patch(SETTINGS, json={"auto_confirm": True})
        assert rejected.status_code == 400, rejected.text
        assert await cache.find(key) == cached

        assert (
            await client.patch(SETTINGS, json={"digits": 3})
        ).status_code == 200
        assert await cache.find(key) is None
        assert (await client.get(SETTINGS)).json()["data"] == DEFAULT | {
            "digits": 3
        }
        cached = await cache.find(key)
        assert cached is not None
        assert cached.digits == 3
    finally:
        app.dependency_overrides.pop(current_admin, None)
