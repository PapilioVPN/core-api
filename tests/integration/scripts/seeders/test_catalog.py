"""Exercise catalog data seeds on a native PostgreSQL transaction."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import select, update
from sqlmodel import col

from scripts.seeders.registry import Seed, registered_seeds, select_seeds
from scripts.seeders.run import SeedResult, execute_seeds
from src.apps.catalog.categories.infra.pg.tables import CategoryTable

pytestmark = pytest.mark.integration


async def test_seed_replays(app: FastAPI, client: AsyncClient) -> None:
    seeds = registered_seeds()
    plan = select_seeds(seeds, ["catalog.bindings"])
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        unit = await scope.get(PGUnitOfWork)
        with pytest.raises(RuntimeError, match="undo catalog seed fixture"):
            async with unit.transaction():
                first = await execute_seeds(unit, plan)
                assert first == [
                    SeedResult("catalog.categories", 1),
                    SeedResult("catalog.attributes", 2),
                    SeedResult("catalog.bindings", 2),
                ]

                category = col(CategoryTable.slug) == "subscriptions"
                stmt = (
                    update(CategoryTable)
                    .where(category)
                    .values(title="Edited by operator")
                )
                await unit.execute(stmt)
                again = await execute_seeds(
                    unit, select_seeds(seeds, ["catalog"])
                )
                assert again == [
                    SeedResult("catalog.scopes", 1),
                    *(SeedResult(seed.key, 0) for seed in plan),
                ]
                stmt = select(col(CategoryTable.title)).where(category)
                result = await unit.execute(stmt)
                assert result.scalar_one() == "Edited by operator"
                raise RuntimeError("undo catalog seed fixture")


async def test_failed_seed_rolls_back(
    app: FastAPI, client: AsyncClient
) -> None:
    async def fail(_unit: PGUnitOfWork) -> int:
        raise ValueError("seed failed")

    plan = registered_seeds()
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        unit = await scope.get(PGUnitOfWork)
        with pytest.raises(ValueError, match="seed failed"):
            await execute_seeds(unit, (*plan, Seed("test.failure", fail)))

        with pytest.raises(RuntimeError, match="undo catalog seed fixture"):
            async with unit.transaction():
                assert await execute_seeds(unit, plan) == [
                    SeedResult("catalog.scopes", 1),
                    SeedResult("catalog.categories", 1),
                    SeedResult("catalog.attributes", 2),
                    SeedResult("catalog.bindings", 2),
                ]
                raise RuntimeError("undo catalog seed fixture")
