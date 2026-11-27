"""Exercise the Wallex observation and its committed rate update."""

from decimal import Decimal
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.infra.db.uow import UnitOfWork
from papilio.infra.http.connection import HTTPConnection
from papilio.infra.redis.client import RedisClient, resolve
from papilio.utils.dates import utc_now
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.apps.shop.crypto.rates.app.pipelines.refresh import (
    RateRefreshPipeline,
)
from src.apps.shop.crypto.rates.domain.models.records import Rate
from src.apps.shop.crypto.rates.domain.results.records import RateFailure
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration


async def test_refresh_rate(
    app: FastAPI, client: AsyncClient, pg: CoreSettings
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    redis = await container.get(RedisClient | None)
    if redis is None:
        pytest.skip("Set PAPILIOVPN_TEST_REDIS_URL to the isolated test Redis")
    key = "shop:crypto:rates"
    await resolve(redis.client.delete(key))
    connection = await container.get(HTTPConnection)
    original = connection.client
    price = "12345.678901234567890"
    status = 200
    quote = "TMN"

    def market(request: Request) -> Response:
        assert UnitOfWork.current() is None
        assert request.method == "GET"
        assert str(request.url) == "https://api.wallex.ir/v1/markets"
        return Response(
            status,
            json={
                "success": True,
                "result": {
                    "symbols": {
                        "USDTTMN": {
                            "baseAsset": "USDT",
                            "quoteAsset": quote,
                            "stats": {"lastPrice": price},
                        }
                    }
                },
            },
        )

    async with AsyncClient(transport=MockTransport(market)) as upstream:
        connection.client = upstream
        try:
            pipeline = await container.get(RateRefreshPipeline)
            before = utc_now()
            first = await pipeline.run()
            assert isinstance(first, Rate)
            assert first.currency == "USD"
            assert first.source == "wallex_usdt"
            assert first.rial_rate == Decimal("123456.78901234567890")
            assert first.fetched_at is not None
            assert before <= first.fetched_at <= utc_now()
            first_raw = await resolve(redis.client.hget(key, "USD"))
            assert first_raw is not None
            assert await resolve(redis.client.ttl(key)) == -1

            price = "22345.1"
            updated = await pipeline.run()
            assert isinstance(updated, Rate)
            assert updated.rial_rate == Decimal("223451")
            saved_raw = await resolve(redis.client.hget(key, "USD"))
            assert saved_raw is not None and saved_raw != first_raw

            for invalid_price in ("0", "NaN"):
                price = invalid_price
                assert await pipeline.run() is RateFailure.INVALID_RATE
            price = "22345.1"
            quote = "IRR"
            assert await pipeline.run() is RateFailure.INVALID_RATE
            quote = "TMN"
            status = 503
            assert await pipeline.run() is RateFailure.MARKET_UNAVAILABLE
        finally:
            connection.client = original

    assert await resolve(redis.client.hget(key, "USD")) == saved_raw
    assert pg.db is not None
    engine = create_async_engine(pg.db.dsn)
    try:
        async with engine.connect() as db:
            stmt = text("SELECT to_regclass('tbl_crypto_rates')")
            assert await db.scalar(stmt) is None
    finally:
        await engine.dispose()
