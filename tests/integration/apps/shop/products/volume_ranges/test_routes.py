"""Exercise configurable volume sales at their HTTP entrypoints."""

from asyncio import gather
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate

pytestmark = pytest.mark.integration


async def test_volume_ranges(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    password = "isolated-volume-ranges-test-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key="ranges-admin", title="Ranges Admin")
        )
        users = await scope.get(IUserCreateCommand)
        admin = await users.create(
            UserCreate(
                first_name="Ranges",
                last_name="Admin",
                mobile="09120000048",
                role_id=role.id,
                password=password,
            ),
            super_admin=True,
        )
    login = await client.post(
        "/admin/auth/tokens",
        json={"mobile": admin.mobile, "password": password},
    )
    assert login.status_code == 200, login.text
    headers = {
        "Authorization": f"Bearer {login.json()['data']['access_token']}"
    }

    gib = 1024**3
    services = "/admin/services"
    service = await client.post(
        services, json={"title": "Custom Traffic"}, headers=headers
    )
    assert service.status_code == 201, service.text
    service_id = service.json()["data"]["id"]
    admin_url = f"{services}/{service_id}/volume-ranges"
    public = f"/public/services/{service_id}"
    ranges = f"{public}/volume-ranges"
    quote = f"{ranges}/quote"
    fixed = {
        "min_bytes": 10 * gib,
        "max_bytes": 30 * gib,
        "step_bytes": 5 * gib,
        "min_days": 7,
        "max_days": 31,
        "step_days": 2,
        "price_per_gib": 5000,
    }
    posted, conflict = sorted(
        await gather(
            client.post(admin_url, json=fixed, headers=headers),
            client.post(admin_url, json=fixed, headers=headers),
        ),
        key=lambda response: response.status_code,
    )
    assert posted.status_code == 201, posted.text
    assert conflict.status_code == 409, conflict.text
    first = posted.json()["data"]
    path = f"{admin_url}/{first['id']}"
    record = await client.get(path, headers=headers)
    assert record.json()["data"] == first

    forever = {
        "min_bytes": 35 * gib,
        "max_bytes": 100 * gib,
        "step_bytes": 5 * gib,
        "price_per_gib": 6000,
        "is_active": False,
    }
    posted = await client.post(admin_url, json=forever, headers=headers)
    assert posted.status_code == 201, posted.text
    second = posted.json()["data"]
    assert second["min_days"] is None and second["step_days"] is None
    other = await client.post(
        services, json={"title": "Another Custom Service"}, headers=headers
    )
    assert other.status_code == 201, other.text
    other_url = f"{services}/{other.json()['data']['id']}/volume-ranges"
    sibling = await client.post(other_url, json=fixed, headers=headers)
    assert sibling.status_code == 201, sibling.text
    cross_parent = await client.get(
        f"{other_url}/{first['id']}", headers=headers
    )
    assert cross_parent.status_code == 404, cross_parent.text

    outside = await client.put(
        path,
        json={**fixed, "max_bytes": 35 * gib},
        headers=headers,
    )
    assert outside.status_code == 409, outside.text
    response = await client.get(
        admin_url,
        params={"volume_bytes": 20 * gib},
        headers=headers,
    )
    assert response.json()["data"] == [first]

    for invalid, status in (
        ({**forever, "min_days": 3}, 400),
        ({**forever, "max_bytes": 97 * gib}, 400),
        ({**forever, "price_per_gib": 1}, 400),
        ({**forever, "step_bytes": gib // 2}, 422),
    ):
        rejected = await client.post(admin_url, json=invalid, headers=headers)
        assert rejected.status_code == status, rejected.text

    offer = await client.post(
        "/admin/catalogs",
        json={
            "title": "Fixed Offer",
            "service_id": service_id,
            "status": "published",
            "price": 10000,
        },
        headers=headers,
    )
    assert offer.status_code == 201, offer.text
    offer_path = f"/public/catalogs/{offer.json()['data']['id']}"
    assert (await client.get(offer_path)).status_code == 200
    visible = await client.get(ranges)
    assert visible.status_code == 200, visible.text
    assert [row["id"] for row in visible.json()["data"]] == [first["id"]]
    assert (
        await client.get(quote, params={"volume_bytes": 35 * gib})
    ).status_code == 404
    second_path = f"{admin_url}/{second['id']}"
    enabled = await client.put(
        second_path, json={**forever, "is_active": True}, headers=headers
    )
    assert enabled.status_code == 200, enabled.text
    available = await client.get(ranges)
    assert available.status_code == 200, available.text
    assert [row["id"] for row in available.json()["data"]] == [
        first["id"],
        second["id"],
    ]

    quoted = await client.get(
        quote, params={"volume_bytes": 20 * gib, "days": 15}
    )
    assert quoted.status_code == 200, quoted.text
    assert quoted.json()["data"] == {
        "range_id": first["id"],
        "volume_bytes": 20 * gib,
        "days": 15,
        "price": 100000,
    }
    quoted = await client.get(quote, params={"volume_bytes": 35 * gib})
    assert quoted.status_code == 200, quoted.text
    assert quoted.json()["data"]["days"] is None
    assert quoted.json()["data"]["price"] == 210000

    for selection in (
        {"volume_bytes": 21 * gib, "days": 15},
        {"volume_bytes": 20 * gib, "days": 14},
        {"volume_bytes": 20 * gib},
        {"volume_bytes": 35 * gib, "days": 7},
    ):
        rejected = await client.get(quote, params=selection)
        assert rejected.status_code == 400, rejected.text

    changed = await client.put(
        path, json={**fixed, "price_per_gib": 5500}, headers=headers
    )
    assert changed.status_code == 200, changed.text
    quoted = await client.get(
        quote, params={"volume_bytes": 20 * gib, "days": 15}
    )
    assert quoted.json()["data"]["price"] == 110000

    for target, rule in ((path, fixed), (second_path, forever)):
        paused = await client.put(
            target, json={**rule, "is_active": False}, headers=headers
        )
        assert paused.status_code == 200, paused.text
    assert (await client.get(ranges)).json()["data"] == []
    assert (await client.get(offer_path)).status_code == 200

    resumed = await client.put(
        second_path, json={**forever, "is_active": True}, headers=headers
    )
    assert resumed.status_code == 200, resumed.text
    offer_id = offer.json()["data"]["id"]
    stopped = await client.patch(
        f"/admin/catalogs/{offer_id}",
        json={"status": "paused"},
        headers=headers,
    )
    assert stopped.status_code == 200, stopped.text
    assert (await client.get(offer_path)).status_code == 404
    assert (
        await client.get(quote, params={"volume_bytes": 35 * gib})
    ).is_success

    removed = await client.delete(path, headers=headers)
    assert removed.status_code == 200, removed.text
    assert (await client.get(path, headers=headers)).status_code == 404

    paused_service = await client.patch(
        f"{services}/{service_id}", json={"is_active": False}, headers=headers
    )
    assert paused_service.is_success, paused_service.text
    assert (await client.get(ranges)).status_code == 404
    hidden = await client.get(quote, params={"volume_bytes": 35 * gib})
    assert hidden.status_code == 404, hidden.text
