"""Verify internal payment creation and its durable gateway reference."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import ConflictException, NotFoundException
from papilio.infra.db.transaction import transaction
from pydantic import ValidationError

from src.apps.shop.crypto.gateways.app.interfaces.services import (
    ICryptoGatewayService,
)
from src.apps.shop.crypto.gateways.domain.dtos.records import GatewayCreate
from src.apps.shop.crypto.payments.app.commands.create import (
    PaymentCreateCommand,
)
from src.apps.shop.crypto.payments.domain.dtos.records import PaymentCreate
from src.apps.shop.crypto.payments.infra.pg.repositories.crud import (
    CryptoPaymentRepository,
)

pytestmark = pytest.mark.integration


async def test_create_payment(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        gateways = await scope.get(ICryptoGatewayService)
        active = await gateways.create(
            GatewayCreate(kind="plisio", title="Active test", is_active=True)
        )
        inactive = await gateways.create(
            GatewayCreate(kind="plisio", title="Inactive test")
        )
        active_id, inactive_id = active.id, inactive.id
        command = await scope.get(PaymentCreateCommand)

        with pytest.raises(NotFoundException):
            await command.create(PaymentCreate(gateway_id=2**63 - 1, amount=1))
        with pytest.raises(ConflictException) as failure:
            await command.create(
                PaymentCreate(gateway_id=inactive_id, amount=1)
            )
        assert failure.value.message_code == "crypto_gateway_inactive"

        amount = 9_000_000_000
        record = await command.create(
            PaymentCreate(gateway_id=active_id, amount=amount)
        )
        payment_id = record.id
        assert payment_id > 0
        assert record.gateway_id == active_id
        assert record.amount == amount

    async with container() as scope:
        repo = await scope.get(CryptoPaymentRepository)
        async with transaction():
            saved = await repo.get_by_id(payment_id)
        assert saved is not None and saved.amount == amount
        assert saved.gateway_id == active_id

        gateways = await scope.get(ICryptoGatewayService)
        with pytest.raises(ConflictException) as failure:
            await gateways.remove(active_id)
        assert failure.value.message_code == "crypto_gateway_in_use"

    assert (
        await client.post("/admin/crypto-payments", json={})
    ).status_code == 404
    for invalid in (0, -1, True, "1", 2**63):
        with pytest.raises(ValidationError):
            PaymentCreate.model_validate(
                {"gateway_id": active_id, "amount": invalid}
            )
