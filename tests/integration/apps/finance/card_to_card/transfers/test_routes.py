"""Verify that the panel and authenticated hook store bank transfers."""

from datetime import datetime, timedelta
from json import loads
from typing import cast
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork
from papilio.types.constants import INT64_MAX
from papilio.utils.dates import utc_now
from sqlalchemy import select

from src.apps.core.access.auth.domain.enums.permissions import AdminPermission
from src.apps.core.access.auth.domain.results.identity import AdminIdentity
from src.apps.core.access.auth.routers.dependencies.identity import (
    current_admin,
)
from src.apps.finance.banking.banks.domain.models.records import BankModel
from src.apps.finance.banking.banks.infra.pg.repositories.records import (
    BankRepository,
)
from src.apps.finance.banking.payment_cards.domain.models.records import (
    PaymentCardModel,
)
from src.apps.finance.banking.payment_cards.infra.pg.repositories.crud import (
    PaymentCardRepository,
)
from src.apps.finance.card_to_card.api_keys.infra.pg.repositories.crud import (
    APIKeyRepository,
)
from src.apps.finance.card_to_card.payments.infra.pg.repositories.crud import (
    CardPaymentRepository,
)
from src.apps.finance.card_to_card.transfers.app.interfaces import commands
from src.apps.finance.card_to_card.transfers.domain.dtos.records import (
    HookTransferCreate,
)
from src.bootstrap.outbox import pending

pytestmark = pytest.mark.integration
ADMIN = "/admin/card-to-card/transfers"
HOOK = "/hooks/card-to-card/transfers"
KEYS = "/admin/card-to-card/api-keys"
CREATED = "papiliovpn.finance.card_to_card.transfer.created.v1"


async def test_transfer_routes(app: FastAPI, client: AsyncClient) -> None:
    amount = 120_000
    data = {"amount": amount}
    assert (await client.post(ADMIN, json=data)).status_code == 401
    assert (await client.post(HOOK, json=data)).status_code == 401

    operator_id = 17
    grants: dict[str, int] = {"finance": AdminPermission.READ}

    async def admin() -> AdminIdentity:
        return AdminIdentity(operator_id, 1, grants, uuid4(), False)

    app.dependency_overrides[current_admin] = admin
    try:
        assert (await client.post(ADMIN, json=data)).status_code == 403
        grants["finance"] |= AdminPermission.CREATE
        assert (await client.post(ADMIN, json=data)).status_code == 422
        assert (await client.post(HOOK, json=data)).status_code == 401
        invalid = await client.post(
            HOOK, headers={"X-API-Key": "invalid"}, json=data
        )
        assert invalid.status_code == 401
        missing = await client.post(HOOK, json=data)
        assert (
            invalid.json()["error"]["message_code"]
            == (missing.json()["error"]["message_code"])
        )

        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            payments = await scope.get(CardPaymentRepository)
            count = await payments.count()
            banks = await scope.get(BankRepository)
            cards = await scope.get(PaymentCardRepository)
            async with transaction():
                bank = await banks.create(
                    BankModel(code="transfer_cards", title="Transfer Cards")
                )
                card = await cards.create(
                    PaymentCardModel(
                        bank_id=bank.id,
                        card_number="0000000000000018",
                        holder_name="Transfer Test",
                        is_active=False,
                    )
                )

        assert (
            await client.post(ADMIN, json=data | {"card_id": INT64_MAX})
        ).status_code == 404

        for bad_amount in (0, -1, 1.5, "120000", 2**63):
            rejected = await client.post(
                ADMIN, json={"amount": bad_amount, "card_id": card.id}
            )
            assert rejected.status_code == 422, rejected.text
        operator = await client.post(
            ADMIN,
            json=data
            | {"source": "hook", "source_id": 999, "card_id": card.id},
        )
        assert operator.status_code == 201, operator.text
        manual = operator.json()["data"]
        assert manual["amount"] == amount
        assert manual["source"] == "admin"
        assert manual["source_id"] == operator_id
        assert manual["card_id"] == card.id
        assert manual["transferred_at"] is None
        assert manual["created_at"] is not None

        now = utc_now()
        issued = await client.post(
            KEYS,
            json={
                "title": "Transfer feed",
                "expires_at": (now + timedelta(hours=1)).isoformat(),
            },
        )
        assert issued.status_code == 201, issued.text
        credential = issued.json()["data"]
        key_id = credential["api_key"]["id"]
        headers = {"X-API-Key": credential["key"]}
        transferred_at = now - timedelta(minutes=5)
        result = await client.post(
            HOOK,
            headers=headers,
            json=data
            | {
                "transferred_at": transferred_at.isoformat(),
                "source": "admin",
                "source_id": 999,
                "card_number": card.card_number,
            },
        )
        assert result.status_code == 201, result.text
        automatic = result.json()["data"]
        assert automatic["id"] != manual["id"]
        assert automatic["source"] == "hook"
        assert automatic["source_id"] == key_id
        assert automatic["card_id"] == card.id
        assert card.card_number not in result.text
        assert (
            datetime.fromisoformat(automatic["transferred_at"])
            == transferred_at
        )
        assert datetime.fromisoformat(automatic["created_at"]) > transferred_at
        assert (
            await client.post(
                HOOK,
                headers=headers,
                json=data | {"transferred_at": "2025-01-01T12:00:00"},
            )
        ).status_code == 422

        paged = await client.get(
            ADMIN, params={"amount": amount, "per_page": 1}
        )
        assert paged.status_code == 200, paged.text
        assert paged.json()["data"] == [automatic]
        assert paged.json()["meta"]["total_items"] == 2
        empty = await client.get(ADMIN, params={"amount": amount + 1})
        assert empty.status_code == 200
        assert empty.json()["data"] == []
        filtered = await client.get(ADMIN, params={"source": "admin"})
        assert filtered.json()["data"] == [manual]
        details = await client.get(f"{ADMIN}/{automatic['id']}")
        assert details.json()["data"] == automatic
        unknown = await client.post(
            HOOK,
            headers=headers,
            json=data | {"card_number": "0000000000000026"},
        )
        assert unknown.status_code == 400, unknown.text
        no_number = await client.post(
            HOOK, headers=headers, json=data | {"card_id": card.id}
        )
        assert no_number.status_code == 201, no_number.text
        assert no_number.json()["data"]["card_id"] is None
        by_card = await client.get(ADMIN, params={"card_id": card.id})
        assert by_card.json()["data"] == [automatic, manual]

        async with container() as scope:
            payments = await scope.get(CardPaymentRepository)
            assert await payments.count() == count
            keys = await scope.get(APIKeyRepository)
            async with transaction():
                await keys.update_by_id(key_id, {"expires_at": utc_now()})
        assert (
            await client.post(HOOK, headers=headers, json=data)
        ).status_code == 401

        async with container() as scope:
            keys = await scope.get(APIKeyRepository)
            async with transaction():
                await keys.update_by_id(
                    key_id, {"expires_at": now + timedelta(hours=1)}
                )
        grants["finance"] |= AdminPermission.UPDATE
        assert (
            await client.patch(f"{KEYS}/{key_id}/revoke")
        ).status_code == 200
        assert (
            await client.post(HOOK, headers=headers, json=data)
        ).status_code == 401

        async with container() as scope:
            command = await scope.get(commands.IHookTransferCommand)
            with pytest.raises(RuntimeError, match="rollback transfer"):
                async with transaction():
                    await command.create(
                        HookTransferCreate(amount=amount), key_id=key_id
                    )
                    raise RuntimeError("rollback transfer")
            unit = await scope.get(PGUnitOfWork)
            stmt = (
                select(pending.c.payload)
                .where(pending.c.queue == CREATED)
                .order_by(pending.c.id)
            )
            result = await unit.execute(stmt)
            events = [loads(payload)["event"] for payload in result.scalars()]
        assert events == [
            {"transfer_id": manual["id"]},
            {"transfer_id": automatic["id"]},
            {"transfer_id": no_number.json()["data"]["id"]},
        ]
        page = await client.get(ADMIN)
        assert page.json()["meta"]["total_items"] == 3
    finally:
        app.dependency_overrides.pop(current_admin, None)
