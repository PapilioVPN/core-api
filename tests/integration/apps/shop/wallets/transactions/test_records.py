"""Exercise atomic wallet posting and rollback against PostgreSQL."""

from asyncio import gather
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import NotFoundException, ValidationException
from papilio.infra.db.uow import PGUnitOfWork
from papilio.types.constants import INT64_MAX
from sqlalchemy import func
from sqlmodel import col, select

from src.apps.core.access.roles.app.interfaces.services import IRoleService
from src.apps.core.access.roles.domain.dtos.records import RoleCreate
from src.apps.core.access.users.app.interfaces.commands import (
    IUserCreateCommand,
)
from src.apps.core.access.users.domain.dtos.records import UserCreate
from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)
from src.apps.shop.customers.profiles.domain.dtos.records import ProfileCreate
from src.apps.shop.wallets.balance.app.interfaces.services import (
    IWalletBalanceService,
)
from src.apps.shop.wallets.transactions.app.interfaces.commands import (
    IWalletCreditCommand,
    IWalletDebitCommand,
)
from src.apps.shop.wallets.transactions.app.interfaces.services import (
    IWalletTransactionService,
)
from src.apps.shop.wallets.transactions.domain.dtos.records import (
    TransactionPost,
)
from src.apps.shop.wallets.transactions.domain.enums.records import Direction
from src.apps.shop.wallets.transactions.domain.models.records import (
    WalletTransactionModel,
)
from src.apps.shop.wallets.transactions.infra.pg.repositories.crud import (
    WalletTransactionRepository,
)
from src.apps.shop.wallets.transactions.infra.pg.tables import (
    WalletTransactionTable,
)

pytestmark = pytest.mark.integration


async def _customer(container: AsyncContainer) -> int:
    async with container() as scope:
        customers = await scope.get(ICustomerService)
        customer = await customers.create(
            ProfileCreate(name="Ledger Customer")
        )
        id = customer.id
    return id


async def _post(
    container: AsyncContainer,
    customer_id: int,
    data: TransactionPost,
    *,
    direction: Direction = Direction.CREDIT,
) -> WalletTransactionModel:
    async with container() as scope:
        if direction == Direction.CREDIT:
            credit = await scope.get(IWalletCreditCommand)
            row = await credit.credit(customer_id, data)
        else:
            debit = await scope.get(IWalletDebitCommand)
            row = await debit.debit(customer_id, data)
    return row


async def _current(
    container: AsyncContainer, customer_id: int
) -> tuple[int | None, int]:
    async with container() as scope:
        balances = await scope.get(IWalletBalanceService)
        unit = await scope.get(PGUnitOfWork)
        wallet = await balances.find(customer_id)
        table = WalletTransactionTable
        stmt = (
            select(func.count())
            .select_from(table)
            .where(col(table.customer_id) == customer_id)
        )
        rows = await unit.execute(stmt)
        amount = wallet.amount if wallet is not None else None
        count = rows.scalar_one()
    return amount, count


async def test_posting_updates_balance(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    id = await _customer(container)
    credit = TransactionPost(amount=100, description="Wallet credit")
    with pytest.raises(NotFoundException):
        await _post(container, id, credit, direction=Direction.DEBIT)
    assert await _current(container, id) == (None, 0)

    row = await _post(container, id, credit)
    assert row.customer_id == id
    assert row.direction == Direction.CREDIT and row.amount == 100
    assert (row.balance_before, row.balance_after) == (0, 100)
    assert row.description == "Wallet credit"
    assert await _current(container, id) == (100, 1)

    other = await _customer(container)
    async with container() as scope:
        transactions = await scope.get(IWalletTransactionService)
        saved = await transactions.find(id, row.id)
        assert saved is not None and saved.description == "Wallet credit"
        assert (saved.balance_before, saved.balance_after) == (0, 100)
        assert await transactions.find(other, row.id) is None
        assert not hasattr(transactions, "add")

    debit = TransactionPost(amount=70)
    results = await gather(
        _post(container, id, debit, direction=Direction.DEBIT),
        _post(container, id, debit, direction=Direction.DEBIT),
        return_exceptions=True,
    )
    successes = [
        result
        for result in results
        if isinstance(result, WalletTransactionModel)
    ]
    failures = [
        result for result in results if isinstance(result, ValidationException)
    ]
    assert len(successes) == len(failures) == 1
    assert (successes[0].balance_before, successes[0].balance_after) == (
        100,
        30,
    )
    assert failures[0].message_code == "wallet_insufficient_balance"
    assert failures[0].loc == ["amount"]
    assert await _current(container, id) == (30, 2)


async def test_concurrent_credits_record_consecutive_balances(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    id = await _customer(container)
    rows = await gather(
        _post(container, id, TransactionPost(amount=65)),
        _post(container, id, TransactionPost(amount=35)),
    )
    first, second = sorted(rows, key=lambda row: row.balance_before)
    assert first.balance_before == 0
    assert first.balance_after == first.amount == second.balance_before
    assert second.balance_after == 100
    assert await _current(container, id) == (100, 2)


async def test_credit_overflow_rolls_back(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    id = await _customer(container)
    async with container() as scope:
        balances = await scope.get(IWalletBalanceService)
        await balances.open(id)
    await _post(
        container,
        id,
        TransactionPost(amount=INT64_MAX),
    )
    with pytest.raises(ValidationException) as error:
        await _post(
            container,
            id,
            TransactionPost(amount=1),
        )
    assert error.value.message_code == "wallet_balance_limit"
    assert error.value.loc == ["amount"]
    assert await _current(container, id) == (INT64_MAX, 1)


async def test_insert_failure_rolls_back_balance(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    id = await _customer(container)
    async with container() as scope:
        balances = await scope.get(IWalletBalanceService)
        await balances.open(id)

    async def fail_insert(
        repo: WalletTransactionRepository, data: WalletTransactionModel
    ) -> WalletTransactionModel:
        raise RuntimeError("wallet transaction insert failed")

    monkeypatch.setattr(WalletTransactionRepository, "create", fail_insert)
    with pytest.raises(RuntimeError, match="wallet transaction insert failed"):
        await _post(
            container,
            id,
            TransactionPost(amount=100),
        )
    assert await _current(container, id) == (0, 0)


async def _headers(
    app: FastAPI, client: AsyncClient, *, super_admin: bool
) -> dict[str, str]:
    container = cast(AsyncContainer, app.state.dishka_container)
    suffix = 91 if super_admin else 92
    mobile = f"091770000{suffix}"
    password = "isolated-wallet-operator-password"
    async with container() as scope:
        roles = await scope.get(IRoleService)
        role = await roles.create(
            RoleCreate(key=f"wallet-test-{suffix}", title="Wallet Operator")
        )
        users = await scope.get(IUserCreateCommand)
        await users.create(
            UserCreate(
                first_name="Wallet",
                last_name="Operator",
                mobile=mobile,
                password=password,
                role_id=role.id,
            ),
            super_admin=super_admin,
        )
    response = await client.post(
        "/admin/auth/tokens", json={"mobile": mobile, "password": password}
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_admin_credit_and_debit(
    app: FastAPI, client: AsyncClient
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    id = await _customer(container)
    path = f"/admin/wallets/{id}"
    data = {"amount": 100, "description": "Operator credit"}
    assert (await client.post(f"{path}/credits", json=data)).status_code == 401
    forbidden = await _headers(app, client, super_admin=False)
    assert (
        await client.post(f"{path}/credits", headers=forbidden, json=data)
    ).status_code == 403
    assert await _current(container, id) == (None, 0)

    headers = await _headers(app, client, super_admin=True)
    response = await client.post(f"{path}/credits", headers=headers, json=data)
    assert response.status_code == 201, response.text
    credit = response.json()["data"]
    assert credit["customer_id"] == id and credit["direction"] == "credit"
    assert (credit["balance_before"], credit["balance_after"]) == (0, 100)
    assert (
        credit["amount"] == 100
        and credit["description"] == data["description"]
    )
    assert await _current(container, id) == (100, 1)

    response = await client.post(
        f"{path}/debits", headers=headers, json={"amount": 101}
    )
    assert response.status_code == 400, response.text
    error = response.json()["error"]
    assert error["loc"] == ["amount"]
    assert error["message_code"] == "wallet_insufficient_balance"
    assert await _current(container, id) == (100, 1)
    response = await client.post(
        f"{path}/debits", headers=headers, json={"amount": 30}
    )
    assert response.status_code == 201, response.text
    debit = response.json()["data"]
    assert debit["direction"] == "debit" and debit["amount"] == 30
    assert (debit["balance_before"], debit["balance_after"]) == (100, 70)
    assert debit["description"] is None
    assert await _current(container, id) == (70, 2)
