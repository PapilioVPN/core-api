"""Register and read immutable Xray revisions through the operator API."""

from asyncio import gather
from hashlib import sha256
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork
from papilio.security.crypto import decrypt, encrypt
from sqlalchemy import update
from sqlmodel import col, select

from src.apps.network.engines.xray.infra.pg.tables import XrayRevisionTable
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration

PATH = "/admin/xray/revisions"


async def test_revisions_are_immutable_and_idempotent(
    pg: CoreSettings, app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000920", role_key="xray-revisions"
    )
    source = '{ "remarks": "isolated-پیشنهاد" }\n'
    body = {"config_json": source}
    assert (await client.post(PATH, json=body)).status_code == 401

    first, second = await gather(
        client.post(PATH, headers=headers, json=body),
        client.post(PATH, headers=headers, json=body),
    )
    assert sorted([first.status_code, second.status_code]) == [200, 201], (
        first.text,
        second.text,
    )
    row = first.json()["data"]
    assert second.json()["data"] == row
    assert row == {
        "id": row["id"],
        "config_sha256": sha256(source.encode()).hexdigest(),
        "size_bytes": len(source.encode()),
        "created_at": row["created_at"],
    }
    id = row["id"]

    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        uow = await scope.get(PGUnitOfWork)
        stmt = select(col(XrayRevisionTable.ciphertext)).where(
            col(XrayRevisionTable.id) == id
        )
        sealed = (await uow.execute(stmt)).scalar_one()
    assert pg.crypto is not None
    assert sealed != source
    assert (
        decrypt(sealed, pg.crypto.encryption_key).encode() == source.encode()
    )

    detail = await client.get(f"{PATH}/{id}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"] == row
    missing = await client.get(f"{PATH}/9999999", headers=headers)
    assert missing.status_code == 404, missing.text
    assert (
        await client.patch(f"{PATH}/{id}", headers=headers, json=body)
    ).status_code == 405
    for invalid in ("not-json", "[]", '{"value": NaN}'):
        result = await client.post(
            PATH, headers=headers, json={"config_json": invalid}
        )
        assert result.status_code == 422, result.text
        assert invalid not in result.text

    alternate = source.rstrip()
    changed = await client.post(
        PATH, headers=headers, json={"config_json": alternate}
    )
    assert changed.status_code == 201, changed.text
    assert changed.json()["data"]["id"] != id
    assert (
        changed.json()["data"]["config_sha256"]
        == sha256(alternate.encode()).hexdigest()
    )
    page = await client.get(PATH, headers=headers, params={"per_page": 1})
    assert page.status_code == 200, page.text
    assert page.json()["data"][0] == changed.json()["data"]
    assert page.json()["meta"]["total_items"] >= 2

    # A valid encrypted value from other bytes cannot stand in for this ID.
    different = source.replace("isolated-", "archived-")
    assert len(different.encode()) == len(source.encode())
    async with container() as scope:
        uow = await scope.get(PGUnitOfWork)
        stmt = (
            update(XrayRevisionTable)
            .where(col(XrayRevisionTable.id) == id)
            .values(ciphertext=encrypt(different, pg.crypto.encryption_key))
        )
        async with uow.transaction():
            await uow.execute(stmt)
    validation_url = (
        f"/admin/nodes/9999999/xray/instances/edge/config-revisions/{id}"
        "/validations"
    )
    corrupted = await client.post(validation_url, headers=headers)
    assert corrupted.status_code == 503, corrupted.text
    assert corrupted.json()["error"]["message_code"] == (
        "xray_revision_source_unavailable"
    )
    assert "archived-" not in corrupted.text
