"""Manage receiving cards through the native admin API."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from scripts.seeders.registry import registered_seeds, select_seeds
from scripts.seeders.run import run_seeds
from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.banking.payment_cards.app.interfaces.queries import (
    ICardPickQuery,
)
from src.apps.shop.banking.payment_cards.domain.enums.records import (
    PaymentMode,
)
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration

CARDS = "/admin/payment-cards"
BANKS = "/admin/banks"
PREFIXES = "/admin/card-prefixes"


def card_number(prefix: str) -> str:
    """Generate a synthetic valid test number with the chosen prefix."""
    body = prefix.ljust(15, "0")
    checksum = sum(
        sum(map(int, str(int(digit) * (2 if index % 2 == 0 else 1))))
        for index, digit in enumerate(body)
    )
    return body + str(-checksum % 10)


def card(number: str, holder: str) -> dict[str, str]:
    return {"card_number": number, "holder_name": holder}


async def picked(app: FastAPI, mode: PaymentMode) -> int | None:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        query = await scope.get(ICardPickQuery)
        record = await query.pick(mode)
    return record.id if record is not None else None


@pytest.fixture
async def headers(app: FastAPI, client: AsyncClient) -> dict[str, str]:
    password = "isolated-banking-test-password"
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(RoleCreate(key="banking", title="Banking"))
        users = await scope.get(IUserCreateCommand)
        user = await users.create(
            UserCreate(
                first_name="Banking",
                last_name="Operator",
                role_id=role.id,
                mobile="09120000056",
                password=password,
            ),
            super_admin=True,
        )
    result = await client.post(
        "/admin/auth/tokens",
        json={"mobile": user.mobile, "password": password},
    )
    assert result.status_code == 200, result.text
    return {"Authorization": f"Bearer {result.json()['data']['access_token']}"}


async def test_payment_cards(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    headers: dict[str, str],
) -> None:
    assert (await client.get(CARDS)).status_code == 401
    assert (await client.get(PREFIXES)).status_code == 401
    assert (await client.get("/public/payment-cards")).status_code == 404
    assert await picked(app, PaymentMode.MANUAL) is None

    assert pg.db is not None
    seeds = select_seeds(registered_seeds(), ["banking.card_prefixes"])
    result = await run_seeds(pg.db, seeds)
    assert [(row.key, row.inserted) for row in result] == [
        ("banking.banks", 38),
        ("banking.card_prefixes", 55),
    ]
    assert [row.inserted for row in await run_seeds(pg.db, seeds)] == [0, 0]
    bank = await client.get(f"{BANKS}/prefix/62198618", headers=headers)
    assert bank.status_code == 200, bank.text
    assert bank.json()["data"]["code"] == "IR-056"
    melli = await client.get(
        BANKS, headers=headers, params={"q": "IR-017", "is_active": True}
    )
    assert melli.status_code == 200
    melli_id = melli.json()["data"][0]["id"]
    assert melli.json()["meta"]["total_items"] == 1
    saman_id = bank.json()["data"]["id"]

    base_prefix = await client.get(
        f"{PREFIXES}/prefix", headers=headers, params={"prefix": "621986"}
    )
    assert base_prefix.status_code == 200
    base = base_prefix.json()["data"]
    assert base["bank_id"] == saman_id
    page = await client.get(
        PREFIXES,
        headers=headers,
        params={"bank_id": saman_id, "is_active": True},
    )
    assert {row["prefix"] for row in page.json()["data"]} == {
        "621986",
        "62198618",
        "62198619",
    }
    matches = await client.get(
        f"{PREFIXES}/prefixes/batch",
        headers=headers,
        params={"prefixes": ["621986", "621986", "999998"]},
    )
    assert matches.json()["data"] == [base]
    prefix = await client.post(
        PREFIXES,
        headers=headers,
        json={"bank_id": melli_id, "prefix": "62198642"},
    )
    assert prefix.status_code == 201
    prefix_id = prefix.json()["data"]["id"]
    longest = await client.get(f"{BANKS}/prefix/62198642", headers=headers)
    assert longest.json()["data"]["id"] == melli_id

    manual_number = card_number("62198642")
    auto_number = card_number("62198618")
    unknown_number = card_number("999998")
    invalid_number = manual_number[:-1] + str(
        (int(manual_number[-1]) + 1) % 10
    )
    for number, code in (
        (unknown_number, 400),
        (card_number("636214"), 400),
        (invalid_number, 422),
    ):
        invalid = await client.post(
            CARDS, headers=headers, json=card(number, "Invalid Destination")
        )
        assert invalid.status_code == code
        assert number not in invalid.text

    manual = await client.post(
        CARDS, headers=headers, json=card(manual_number, "Manual Destination")
    )
    assert manual.status_code == 201
    saved = manual.json()["data"]
    assert saved["bank_id"] == melli_id
    assert saved["allow_manual"] is True
    assert saved["allow_auto"] is False
    path = f"{CARDS}/{saved['id']}"
    duplicate = await client.post(
        CARDS, headers=headers, json=card(manual_number, "Duplicate")
    )
    assert duplicate.status_code == 409
    assert manual_number not in duplicate.text

    auto = await client.post(
        CARDS,
        headers=headers,
        json=card(auto_number, "Auto Destination")
        | {"allow_manual": False, "allow_auto": True},
    )
    assert auto.status_code == 201
    automatic = auto.json()["data"]
    assert automatic["bank_id"] == saman_id
    assert await picked(app, PaymentMode.MANUAL) == saved["id"]
    assert await picked(app, PaymentMode.AUTO) == automatic["id"]

    page = await client.get(
        CARDS,
        headers=headers,
        params={"q": "destination", "bank_id": melli_id, "allow_auto": False},
    )
    assert page.json()["meta"]["total_items"] == 1
    assert page.json()["data"] == [saved]
    batch = await client.get(
        f"{CARDS}/batch",
        headers=headers,
        params={"ids": [saved["id"], saved["id"], 99999]},
    )
    assert batch.json()["data"] == [saved]
    assert (await client.get(path, headers=headers)).json()["data"] == saved

    paused_prefix = await client.patch(
        f"{PREFIXES}/{prefix_id}", headers=headers, json={"is_active": False}
    )
    assert paused_prefix.status_code == 200
    assert await picked(app, PaymentMode.MANUAL) is None
    assert await picked(app, PaymentMode.AUTO) == automatic["id"]
    assert (
        await client.delete(f"{PREFIXES}/{prefix_id}", headers=headers)
    ).status_code == 200
    assert await picked(app, PaymentMode.MANUAL) is None

    duplicate = await client.patch(
        path, headers=headers, json={"card_number": auto_number}
    )
    assert duplicate.status_code == 409
    assert auto_number not in duplicate.text
    assert (await client.get(path, headers=headers)).json()["data"] == saved
    changed = await client.patch(
        path,
        headers=headers,
        json={"card_number": manual_number, "allow_auto": True},
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["bank_id"] == saman_id
    assert changed.json()["data"]["allow_manual"] is True
    assert await picked(app, PaymentMode.MANUAL) == saved["id"]
    assert await picked(app, PaymentMode.AUTO) in {
        saved["id"],
        automatic["id"],
    }

    paused = await client.patch(
        path, headers=headers, json={"is_active": False}
    )
    assert paused.status_code == 200
    assert await picked(app, PaymentMode.MANUAL) is None
    assert await picked(app, PaymentMode.AUTO) == automatic["id"]
    removed = await client.delete(path, headers=headers)
    assert removed.status_code == 200
    assert (await client.get(path, headers=headers)).status_code == 404

    historical = await client.patch(
        f"{PREFIXES}/{base['id']}", headers=headers, json={"is_active": False}
    )
    assert historical.status_code == 200
    assert [row.inserted for row in await run_seeds(pg.db, seeds)] == [0, 0]
    exact = await client.get(f"{PREFIXES}/{base['id']}", headers=headers)
    assert exact.json()["data"]["is_active"] is False
