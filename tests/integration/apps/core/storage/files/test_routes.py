"""Exercise the copied storage feature through native HTTP and SDK paths."""

from collections.abc import AsyncIterator
from hashlib import sha256
from pathlib import Path
from typing import cast

import pytest
from anyio.streams.file import FileReadStream
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import HttpUrl

from src.apps.core.auth.domain.enums.permissions import AdminPermission
from src.apps.core.roles.app.interfaces.services import (
    IRoleScopeService,
    IRoleService,
)
from src.apps.core.roles.domain.dtos.records import RoleCreate
from src.apps.core.roles.domain.dtos.role_scopes import RoleScopeCreate
from src.apps.core.scopes.app.interfaces.services import IScopeService
from src.apps.core.scopes.domain.dtos.records import ScopeCreate
from src.apps.core.storage.files.app.interfaces.uploads import IFileUpload
from src.apps.core.storage.files.domain.dtos.uploads import FileUpload
from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.users.app.interfaces.commands import IUserCreateCommand
from src.apps.core.users.domain.dtos.records import UserCreate
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration
CONFIG = "/admin/storage/config"
FILES = "/admin/storage/files"
PROVIDERS = "/admin/storage/providers"
LOCAL_URL = "https://media.example.org/files/"


@pytest.fixture
def pg(pg: CoreSettings, tmp_path: Path) -> CoreSettings:
    pg.storage.path = str(tmp_path / "media")
    pg.storage.temp_dir = str(tmp_path / "staging")
    pg.storage.max_file_size = 1024
    pg.storage.public_base_url = HttpUrl(LOCAL_URL)
    return pg


async def test_storage_authorization(client: AsyncClient) -> None:
    for path in (CONFIG, FILES, PROVIDERS):
        assert (await client.get(path)).status_code == 401


async def test_local_and_s3(
    app: FastAPI,
    client: AsyncClient,
    tmp_path: Path,
    s3_config: S3Config,
) -> None:
    password = "isolated-storage-operator-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="storage-test", title="Storage Operator")
        )
        role_id = role.id
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Storage",
                last_name="Operator",
                role_id=role_id,
                mobile="09120000076",
                password=password,
            ),
            super_admin=False,
        )
        mobile = user.mobile
    token = await client.post(
        "/admin/auth/tokens", json={"mobile": mobile, "password": password}
    )
    assert token.status_code == 200
    headers = {
        "Authorization": f"Bearer {token.json()['data']['access_token']}",
        "Accept-Encoding": "identity",
    }
    assert (await client.get(CONFIG, headers=headers)).status_code == 403

    async with container() as scope:
        scopes = await scope.get(IScopeService)
        storage = await scopes.create(
            ScopeCreate(key="storage", title="Storage")
        )
        grants = await scope.get(IRoleScopeService)
        await grants.create(
            role_id,
            RoleScopeCreate(
                scope_id=storage.id,
                permissions=AdminPermission.READ
                | AdminPermission.CREATE
                | AdminPermission.UPDATE
                | AdminPermission.DELETE,
            ),
        )

    assert (await client.get(CONFIG, headers=headers)).status_code == 404
    selected = await client.put(
        CONFIG, headers=headers, json={"backend": "local"}
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["data"]["backend"] == "local"

    uploads = await container.get(IFileUpload)
    data = FileUpload(
        original_name="example.bin", mime_type="application/octet-stream"
    )
    original = tmp_path / "example.bin"
    payload = b"local contents"
    original.write_bytes(payload)
    async with await FileReadStream.from_path(original) as source:
        local = await uploads.upload(source, data, max_bytes=1024)
    digest = sha256(payload).hexdigest()
    assert local.url == f"{LOCAL_URL}{digest[:2]}/{digest}"
    download = await client.get(
        f"{FILES}/{local.file.id}/content", headers=headers
    )
    assert download.status_code == 200, download.text
    assert download.content == payload
    assert download.headers["x-content-type-options"] == "nosniff"
    assert download.headers["content-length"] == str(len(payload))

    async def oversized() -> AsyncIterator[bytes]:
        yield bytes(1024)
        yield b"!"

    invalid = await client.post(
        FILES,
        headers=headers,
        params=data.model_dump(),
        content=oversized(),
    )
    assert invalid.status_code == 413

    provider = await client.post(
        PROVIDERS,
        headers=headers,
        json={
            "key": "s3-test",
            "title": "S3 Test Provider",
            "config": s3_config.model_dump(mode="json"),
        },
    )
    assert provider.status_code == 201, provider.text
    provider_id = provider.json()["data"]["id"]
    config = await client.get(
        f"{PROVIDERS}/{provider_id}/config", headers=headers
    )
    assert config.status_code == 200
    assert config.json()["data"]["config"]["has_aws_secret_access_key"] is True
    assert s3_config.aws_secret_access_key not in config.text
    active = await client.patch(
        f"{PROVIDERS}/{provider_id}/activity",
        headers=headers,
        json={"is_active": True},
    )
    assert active.status_code == 200, active.text
    selected = await client.put(
        CONFIG, headers=headers, json={"backend": "s3"}
    )
    assert selected.status_code == 200, selected.text

    copied = await client.post(
        FILES, headers=headers, params=data.model_dump(), content=payload
    )
    assert copied.status_code == 201, copied.text
    assert copied.json()["data"]["content_id"] == local.file.content_id
    assert copied.json()["data"]["id"] != local.file.id

    remote_payload = b"S3 contents"
    remote = await client.post(
        FILES,
        headers=headers,
        params=data.model_dump(),
        content=remote_payload,
    )
    assert remote.status_code == 201, remote.text
    remote_id = remote.json()["data"]["id"]
    download = await client.get(
        f"{FILES}/{remote_id}/content", headers=headers
    )
    assert download.status_code == 200, download.text
    assert download.content == remote_payload

    rows = await client.get(
        FILES, headers=headers, params={"content_id": local.file.content_id}
    )
    assert rows.json()["meta"]["total_items"] == 2
    assert not list((tmp_path / "staging").iterdir())
