"""Exercise the bounded Xray revision picker against PostgreSQL."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_REVISIONS = "/admin/xray/revisions"
_SELECTION = f"{_REVISIONS}/simple"


async def test_selection_uses_one_projected_read_and_a_stable_cursor(
    app: FastAPI, client: AsyncClient
) -> None:
    assert (await client.get(_SELECTION)).status_code == 401
    headers = await admin_headers(
        app, client, mobile="09120000684", role_key="xray-revision-selector"
    )

    async def save(label: str) -> dict:
        response = await client.post(
            _REVISIONS,
            headers=headers,
            json={"config_json": f'{{"remarks":"revision-picker-{label}"}}'},
        )
        assert response.status_code == 201, response.text
        row = response.json()["data"]
        return {key: row[key] for key in ("id", "config_sha256", "created_at")}

    older = await save("older")
    middle = await save("middle")
    newest = await save("newest")
    captured: list[str] = []

    def capture_sql(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        lowered = statement.lower()
        if "tbl_xray_revisions" in lowered:
            captured.append(lowered)

    event.listen(Engine, "before_cursor_execute", capture_sql)
    try:
        first = await client.get(
            _SELECTION, headers=headers, params={"per_page": 2}
        )
    finally:
        event.remove(Engine, "before_cursor_execute", capture_sql)
    assert first.status_code == 200, first.text
    assert "no-store" in first.headers["Cache-Control"]
    assert first.json()["data"] == [newest, middle]
    assert first.json()["meta"] == {"next_before_id": middle["id"]}
    assert len(captured) == 1, captured
    stmt = captured[0].strip()
    assert stmt.startswith("select") and " limit " in stmt
    assert not any(
        column in stmt for column in ("ciphertext", "size_bytes", "count(")
    )

    inserted = await save("inserted-after-first-page")
    second = await client.get(
        _SELECTION,
        headers=headers,
        params={"per_page": 1, "before_id": middle["id"]},
    )
    assert second.status_code == 200, second.text
    assert second.json()["data"] == [older]
    refreshed = await client.get(
        _SELECTION, headers=headers, params={"per_page": 1}
    )
    assert refreshed.json()["data"] == [inserted]

    catalog = await client.get(
        _REVISIONS, headers=headers, params={"per_page": 1}
    )
    assert catalog.status_code == 200, catalog.text
    end = await client.get(
        _REVISIONS,
        headers=headers,
        params={"page": catalog.json()["meta"]["total_items"], "per_page": 1},
    )
    assert end.status_code == 200, end.text
    last_id = end.json()["data"][0]["id"]
    empty = await client.get(
        _SELECTION, headers=headers, params={"before_id": last_id}
    )
    assert empty.status_code == 200, empty.text
    assert empty.json()["data"] == []
    assert empty.json()["meta"] == {"next_before_id": None}
    for params in ({"before_id": 0}, {"per_page": 101}):
        invalid = await client.get(_SELECTION, headers=headers, params=params)
        assert invalid.status_code == 422, invalid.text
