"""Isolate IPG records between tests in the invocation-owned database."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from src.settings.config import CoreSettings


@pytest.fixture(autouse=True)
async def ipg_records(pg: CoreSettings) -> AsyncIterator[None]:
    assert pg.db is not None
    engine = create_async_engine(pg.db.dsn, poolclass=NullPool)
    try:
        yield
    finally:
        async with engine.begin() as connection:
            await connection.execute(text("DELETE FROM tbl_ipg_payments"))
            await connection.execute(text("DELETE FROM tbl_ipg_configs"))
            await connection.execute(text("DELETE FROM tbl_ipg_gateways"))
        await engine.dispose()
