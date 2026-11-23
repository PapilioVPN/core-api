"""Manage spend thresholds and customer group definitions."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration
URL = "/admin/customer-groups"


@pytest.mark.parametrize("admin", [("071", True)], indirect=True)
async def test_groups(client: AsyncClient, admin: dict[str, str]) -> None:
    assert (await client.get(URL)).status_code == 401
    created = await client.post(
        URL,
        headers=admin,
        json={"key": "standard", "title": "عادی", "min_spend": 0},
    )
    assert created.status_code == 201
    standard = created.json()["data"]
    assert standard["min_spend"] == 0
    path = f"{URL}/{standard['id']}"

    created = await client.post(
        URL,
        headers=admin,
        json={"key": "vip", "title": "VIP", "min_spend": 20_000_000},
    )
    assert created.status_code == 201
    vip = created.json()["data"]
    by_key = await client.get(f"{URL}/key/vip", headers=admin)
    assert by_key.json()["data"] == vip
    duplicate = await client.patch(
        path, headers=admin, json={"min_spend": vip["min_spend"]}
    )
    assert duplicate.status_code == 409
    duplicate = await client.post(
        URL,
        headers=admin,
        json={"key": "vip", "title": "Duplicate", "min_spend": 30_000_000},
    )
    assert duplicate.status_code == 409
    invalid = await client.patch(path, headers=admin, json={"min_spend": -1})
    assert invalid.status_code == 422

    rows = await client.get(
        URL,
        headers=admin,
        params={"q": "vIp", "is_active": True, "per_page": 1},
    )
    assert rows.json()["data"] == [vip]
    assert rows.json()["meta"]["total_items"] == 1

    batch = await client.get(
        f"{URL}/batch",
        headers=admin,
        params={"ids": [standard["id"], standard["id"], 99999]},
    )
    assert batch.json()["data"] == [standard]
    edited = await client.patch(
        path, headers=admin, json={"is_active": False, "min_spend": 500}
    )
    row = edited.json()["data"]
    assert row["is_active"] is False and row["min_spend"] == 500
    assert row["key"] == "standard" and row["title"] == standard["title"]
    assert (await client.get(path, headers=admin)).json()["data"] == row
    assert (await client.delete(path, headers=admin)).status_code == 200
    assert (await client.get(path, headers=admin)).status_code == 404
