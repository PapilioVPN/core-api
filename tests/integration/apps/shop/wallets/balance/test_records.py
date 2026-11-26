"""Verify that each customer has at most one authoritative wallet balance."""

from asyncio import gather
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import NotFoundException
from papilio.infra.db.transaction import transaction
from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import func, select, update
from sqlmodel import col

from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)
from src.apps.shop.customers.profiles.domain.dtos.records import ProfileCreate
from src.apps.shop.wallets.balance.app.interfaces.services import (
    IWalletBalanceService,
)
from src.apps.shop.wallets.balance.infra.pg.tables import WalletBalanceTable

pytestmark = pytest.mark.integration


async def test_open_and_read_wallet_balance(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        customers = await scope.get(ICustomerService)
        customer = await customers.create(ProfileCreate(name="Wallet Owner"))
        other = await customers.create(ProfileCreate(name="No Wallet"))
        customer_id, other_id = customer.id, other.id
        balances = await scope.get(IWalletBalanceService)
        assert await balances.find(customer_id) is None
        with pytest.raises(NotFoundException):
            await balances.open(2**63 - 1)

    async def open_balance() -> tuple[int, int]:
        async with container() as scope:
            balances = await scope.get(IWalletBalanceService)
            balance = await balances.open(customer_id)
            result = balance.customer_id, balance.amount
        return result

    opened = await gather(open_balance(), open_balance())
    assert opened == [(customer_id, 0), (customer_id, 0)]
    table = WalletBalanceTable
    amount = 9_007_199_254_740_993
    async with container() as scope:
        unit = await scope.get(PGUnitOfWork)
        async with transaction():
            stmt = (
                select(func.count())
                .select_from(table)
                .where(col(table.customer_id) == customer_id)
            )
            rows = await unit.execute(stmt)
            assert rows.scalar_one() == 1
            stmt = (
                update(table)
                .where(col(table.customer_id) == customer_id)
                .values(amount=amount)
            )
            await unit.execute(stmt)

    assert await open_balance() == (customer_id, amount)
    async with container() as scope:
        balances = await scope.get(IWalletBalanceService)
        saved = await balances.find(customer_id)
        assert saved is not None and saved.amount == amount
        assert await balances.find(other_id) is None
