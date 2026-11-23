"""Exercise catalog data seeds on a native PostgreSQL transaction."""

from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.uow import PGUnitOfWork
from sqlalchemy import select, update
from sqlmodel import col

from src.apps.catalog.categories.infra.pg.tables import CategoryTable

pytestmark = pytest.mark.integration


async def test_seed_replays(app: FastAPI, client: AsyncClient) -> None:
    from scripts.seeders.catalog import seed_catalog

    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        unit = await scope.get(PGUnitOfWork)
        with pytest.raises(RuntimeError, match="undo catalog seed fixture"):
            async with unit.transaction():
                first = await seed_catalog(unit)
                assert first.categories == 1
                assert first.attributes == first.bindings == 2
                assert first.scopes == 1

                category = col(CategoryTable.slug) == "subscriptions"
                stmt = (
                    update(CategoryTable)
                    .where(category)
                    .values(title="Edited by operator")
                )
                await unit.execute(stmt)
                again = await seed_catalog(unit)
                assert again.categories == again.attributes == 0
                assert again.bindings == again.scopes == 0
                stmt = select(col(CategoryTable.title)).where(category)
                result = await unit.execute(stmt)
                assert result.scalar_one() == "Edited by operator"
                raise RuntimeError("undo catalog seed fixture")
