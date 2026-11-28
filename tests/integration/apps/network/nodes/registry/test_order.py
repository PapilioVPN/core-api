"""Exercise Node display order through both Panel registry entrypoints."""

from asyncio import gather

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from ..auth import admin_headers

pytestmark = pytest.mark.integration
_NODES = "/admin/nodes"
_ORDER = f"{_NODES}/order"
_CHOICES = f"{_NODES}/simple"


async def _node(
    client: AsyncClient,
    headers: dict[str, str],
    label: str,
    *,
    enabled: bool = True,
) -> dict:
    reply = await client.post(
        _NODES,
        headers=headers,
        json={
            "name": f"Node order {label}",
            "address": f"node-order-{label}.example.invalid",
            "port": 8443,
            "is_enabled": enabled,
        },
    )
    assert reply.status_code == 201, reply.text
    return reply.json()["data"]


async def test_reorder_preserves_nonselected_nodes_and_filtered_cursor(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000655", role_key="node-order"
    )
    first = await _node(client, headers, "first")
    untouched = await _node(client, headers, "untouched", enabled=False)
    middle = await _node(client, headers, "middle")
    last = await _node(client, headers, "last")
    selection = [first["id"], last["id"], middle["id"]]
    body = {"ordered_ids": selection}
    unauthorized = await client.put(_ORDER, json=body)
    assert unauthorized.status_code == 401, unauthorized.text
    commands: list[str] = []

    def capture(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        sql = statement.strip().lower()
        if "tbl_nodes" in sql:
            commands.append(sql.split(None, 1)[0])
            assert "api_key_ciphertext" not in sql and "ca_pem" not in sql

    event.listen(Engine, "before_cursor_execute", capture)
    try:
        changed = await client.put(_ORDER, headers=headers, json=body)
        assert changed.status_code == 204, changed.text
        assert commands == ["select", "update"]
        commands.clear()
        repeated = await client.put(_ORDER, headers=headers, json=body)
        assert repeated.status_code == 204, repeated.text
        assert commands == ["select"]
        commands.clear()
        picked = await client.get(
            _CHOICES,
            headers=headers,
            params={"q": "Node order", "is_enabled": True, "per_page": 2},
        )
        assert picked.status_code == 200, picked.text
        assert [row["id"] for row in picked.json()["data"]] == selection[:2]
        assert picked.json()["meta"] == {"next_before_id": last["id"]}
        assert commands == ["select"]
        commands.clear()
        picked = await client.get(
            _CHOICES,
            headers=headers,
            params={
                "q": "Node order",
                "is_enabled": True,
                "per_page": 2,
                "before_id": last["id"],
            },
        )
        assert picked.status_code == 200, picked.text
        assert [row["id"] for row in picked.json()["data"]] == selection[2:]
        assert commands == ["select"]
    finally:
        event.remove(Engine, "before_cursor_execute", capture)

    for values, status in (
        ([last["id"], 99999999, first["id"]], 404),
        ([first["id"], first["id"]], 422),
        ([first["id"]], 422),
        ([True, last["id"]], 422),
    ):
        invalid = await client.put(
            _ORDER, headers=headers, json={"ordered_ids": values}
        )
        assert invalid.status_code == status, invalid.text

    registered = await client.get(
        _NODES, headers=headers, params={"q": "Node order", "per_page": 4}
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["data"] == [first, last, untouched, middle]


async def test_overlap_uses_current_positions(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000656", role_key="node-order-overlap"
    )
    first, middle, last = [
        (await _node(client, headers, f"overlap-{label}"))["id"]
        for label in ("first", "middle", "last")
    ]
    results = await gather(
        client.put(
            _ORDER, headers=headers, json={"ordered_ids": [first, middle]}
        ),
        client.put(
            _ORDER, headers=headers, json={"ordered_ids": [first, last]}
        ),
    )
    assert [result.status_code for result in results] == [204, 204]
    picked = await client.get(
        _CHOICES, headers=headers, params={"q": "Node order overlap"}
    )
    assert picked.status_code == 200, picked.text
    ids = [row["id"] for row in picked.json()["data"]]
    assert ids in ([first, last, middle], [first, middle, last])
