"""Keep the catalog and picker ordered by one PostgreSQL revision policy."""

from asyncio import gather
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_REVISIONS = "/admin/xray/revisions"
_ORDER = f"{_REVISIONS}/order"
_CHOICES = f"{_REVISIONS}/simple"


@contextmanager
def _observe_revision_sql() -> Iterator[list[str]]:
    statements: list[str] = []

    def capture(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        sql = statement.strip().lower()
        if "tbl_xray_revisions" in sql:
            statements.append(sql)

    event.listen(Engine, "before_cursor_execute", capture)
    try:
        yield statements
    finally:
        event.remove(Engine, "before_cursor_execute", capture)


async def test_reorder_preserves_slots_and_picker_cursor(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000651", role_key="xray-revision-order"
    )

    async def create(label: str) -> int:
        response = await client.post(
            _REVISIONS,
            headers=headers,
            json={"config_json": f'{{"remarks":"order-{label}"}}'},
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]["id"]

    oldest = await create("oldest")
    untouched = await create("untouched")
    next_oldest = await create("next-oldest")
    newest = await create("newest")
    body = {"ordered_ids": [oldest, newest, next_oldest]}
    unauthenticated = await client.put(_ORDER, json=body)
    assert unauthenticated.status_code == 401, unauthenticated.text

    with _observe_revision_sql() as statements:
        reordered = await client.put(_ORDER, headers=headers, json=body)
    assert reordered.status_code == 204, reordered.text
    assert not reordered.content
    assert [sql.split(None, 1)[0] for sql in statements] == [
        "select",
        "update",
    ]
    assert not any("ciphertext" in sql for sql in statements)

    reply = await client.get(
        _REVISIONS, headers=headers, params={"per_page": 4}
    )
    assert reply.status_code == 200, reply.text
    expected = [oldest, newest, untouched, next_oldest]
    assert [row["id"] for row in reply.json()["data"]] == expected
    first = await client.get(_CHOICES, headers=headers, params={"per_page": 2})
    assert first.status_code == 200, first.text
    assert [row["id"] for row in first.json()["data"]] == expected[:2]
    assert first.json()["meta"] == {"next_before_id": newest}

    inserted = await create("new-after-page")
    with _observe_revision_sql() as statements:
        following = await client.get(
            _CHOICES,
            headers=headers,
            params={"per_page": 2, "before_id": newest},
        )
    assert following.status_code == 200, following.text
    assert [row["id"] for row in following.json()["data"]] == expected[2:]
    assert len(statements) == 1
    assert not any(
        column in statements[0]
        for column in ("ciphertext", "size_bytes", "count(")
    )
    with _observe_revision_sql() as statements:
        repeated = await client.put(_ORDER, headers=headers, json=body)
    assert repeated.status_code == 204, repeated.text
    assert [sql.split(None, 1)[0] for sql in statements] == ["select"]
    for order in (
        [oldest],
        [oldest, oldest],
        [True, newest],
        [str(oldest), newest],
    ):
        reply = await client.put(
            _ORDER, headers=headers, json={"ordered_ids": order}
        )
        assert reply.status_code == 422, reply.text
    missing = await client.put(
        _ORDER,
        headers=headers,
        json={"ordered_ids": [newest, 9999999, oldest]},
    )
    assert missing.status_code == 404, missing.text
    reply = await client.get(
        _REVISIONS, headers=headers, params={"per_page": 5}
    )
    assert [row["id"] for row in reply.json()["data"]] == [inserted, *expected]


async def test_overlapping_reorders_keep_exact_positions(
    app: FastAPI, client: AsyncClient
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000652", role_key="xray-revision-order-race"
    )
    ids = []
    for label in ("first", "middle", "last"):
        saved = await client.post(
            _REVISIONS,
            headers=headers,
            json={"config_json": f'{{"remarks":"overlapping-order-{label}"}}'},
        )
        assert saved.status_code == 201, saved.text
        ids.append(saved.json()["data"]["id"])
    first, middle, last = ids
    replies = await gather(
        client.put(
            _ORDER, headers=headers, json={"ordered_ids": [first, middle]}
        ),
        client.put(
            _ORDER, headers=headers, json={"ordered_ids": [first, last]}
        ),
    )
    assert [reply.status_code for reply in replies] == [204, 204]
    listed = await client.get(
        _REVISIONS, headers=headers, params={"per_page": 3}
    )
    assert listed.status_code == 200, listed.text
    ordered = [row["id"] for row in listed.json()["data"]]
    assert ordered in ([first, last, middle], [first, middle, last])
    picked = await client.get(
        _CHOICES, headers=headers, params={"per_page": 3}
    )
    assert picked.status_code == 200, picked.text
    assert [row["id"] for row in picked.json()["data"]] == ordered
