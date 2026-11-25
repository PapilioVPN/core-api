"""Exercise the Wallex observation and its committed rate update."""

from decimal import Decimal
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient, MockTransport, Request, Response
from papilio.infra.db.transaction import active_transaction, transaction
from papilio.infra.http.connection import HTTPConnection
from papilio.utils.dates import utc_now

from src.apps.shop.crypto.rates.app.commands.refresh import RateRefreshCommand
from src.apps.shop.crypto.rates.domain.errors import RateUnavailable
from src.apps.shop.crypto.rates.infra.pg.repositories.crud import (
    CryptoRateRepository,
)

pytestmark = pytest.mark.integration


async def test_refresh_rate(app: FastAPI, client: AsyncClient) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    connection = await container.get(HTTPConnection)
    original = connection.client
    price = "12345.678901234567890"
    status = 200
    quote = "TMN"

    def market(request: Request) -> Response:
        assert active_transaction() is None
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
            async with container() as scope:
                command = await scope.get(RateRefreshCommand)
                before = utc_now()
                first = await command.refresh()
                assert first.currency == "USD"
                assert first.source == "wallex_usdt"
                assert first.rial_rate == Decimal("123456.78901234567890")
                assert first.fetched_at is not None
                assert before <= first.fetched_at <= utc_now()
                id = first.id

                price = "22345.1"
                updated = await command.refresh()
                assert updated.id == id
                expected_rate = updated.rial_rate
                fetched_at = updated.fetched_at
                assert expected_rate == Decimal("223451")

                for invalid_price in ("0", "NaN"):
                    price = invalid_price
                    with pytest.raises(RateUnavailable):
                        await command.refresh()
                price = "22345.1"
                quote = "IRR"
                with pytest.raises(RateUnavailable):
                    await command.refresh()
                quote = "TMN"
                status = 503
                with pytest.raises(RateUnavailable):
                    await command.refresh()
        finally:
            connection.client = original

    async with container() as scope:
        repo = await scope.get(CryptoRateRepository)
        async with transaction():
            record = await repo.get_by_id(id)
        assert record is not None
        assert record.rial_rate == expected_rate
        assert record.fetched_at == fetched_at
