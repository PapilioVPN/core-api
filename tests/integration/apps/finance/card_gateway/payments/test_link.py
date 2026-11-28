"""Exercise committed link creation with a controlled Variza transport."""

from asyncio import Event, create_task, wait_for
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from json import loads
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import (
    AsyncClient,
    MockTransport,
    ReadTimeout,
    Request,
    Response,
)
from papilio.infra.db.transaction import active_transaction, transaction
from papilio.infra.http.connection import HTTPConnection
from papilio.utils.dates import utc_now
from pydantic import HttpUrl, SecretStr

from src.apps.finance.card_gateway.gateways.app.interfaces.configs import (
    IConfigService,
    IGatewayConfigCodec,
)
from src.apps.finance.card_gateway.gateways.domain.dtos.configs import (
    VarizaConfig,
)
from src.apps.finance.card_gateway.gateways.domain.enums.records import (
    GatewayKind,
)
from src.apps.finance.card_gateway.gateways.domain.models.configs import (
    ConfigModel,
)
from src.apps.finance.card_gateway.gateways.domain.models.records import (
    GatewayModel,
)
from src.apps.finance.card_gateway.gateways.infra.pg.repositories.crud import (
    GatewayRepository,
)
from src.apps.finance.card_gateway.payments.app.interfaces.link import (
    ICreateLinkCommand,
)
from src.apps.finance.card_gateway.payments.domain.models.records import (
    PaymentModel,
)
from src.apps.finance.card_gateway.payments.domain.results.link import (
    Link,
    LinkFailure,
    LinkResult,
)
from src.apps.finance.card_gateway.payments.infra.pg.repositories.crud import (
    PaymentRepository,
)

pytestmark = pytest.mark.integration
RETURN_URL = HttpUrl("https://shop.example.invalid/paid")


@pytest.fixture
async def payment(
    app: FastAPI, client: AsyncClient
) -> tuple[AsyncContainer, int]:
    container = cast(AsyncContainer, app.state.dishka_container)
    codec = await container.get(IGatewayConfigCodec)
    config = codec.seal(
        VarizaConfig(
            api_key=SecretStr("isolated-variza-api-key"),
            webhook_secret=SecretStr("isolated-webhook-secret"),
            card_last_4="0001",
            expires_in="30m",
        )
    )
    assert config is not None
    async with container() as scope:
        gateways = await scope.get(GatewayRepository)
        configs = await scope.get(IConfigService)
        payments = await scope.get(PaymentRepository)
        async with transaction():
            gateway = await gateways.create(
                GatewayModel(
                    title="Hosted link fixture",
                    kind=GatewayKind.VARIZA,
                    is_active=True,
                )
            )
            await configs.create(ConfigModel(key=gateway.kind, config=config))
            record = await payments.create(
                PaymentModel(gateway_id=gateway.id, amount=120_000)
            )
        id = record.id
    return container, id


@asynccontextmanager
async def mock_variza(
    container: AsyncContainer,
    monkeypatch: pytest.MonkeyPatch,
    transport: MockTransport,
) -> AsyncIterator[None]:
    connection = await container.get(HTTPConnection)
    async with AsyncClient(transport=transport) as client:
        with monkeypatch.context() as patch:
            patch.setattr(connection, "client", client)
            yield


async def test_create_and_reuse_link(
    payment: tuple[AsyncContainer, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    container, id = payment
    command = await container.get(ICreateLinkCommand)
    started, resume = Event(), Event()
    expiry = utc_now() + timedelta(minutes=30)
    slug = "issued-link"
    url = "https://variza.ir/pay/issued-link"
    calls = 0

    async def respond(request: Request) -> Response:
        nonlocal calls
        calls += 1
        assert active_transaction() is None
        assert str(request.url) == "https://variza.ir/api/v1/pay"
        assert request.method == "POST"
        assert (
            request.headers["authorization"]
            == "Bearer isolated-variza-api-key"
        )
        assert loads(request.content) == {
            "amount": 12_000,
            "return_url": str(RETURN_URL),
            "card_last_4": "0001",
            "expires_in": "30m",
        }
        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            stored = await payments.get_by_id(id)
            assert stored is not None and stored.link_requested_at is not None
        started.set()
        await resume.wait()
        return Response(
            201,
            json={
                "slug": slug,
                "pay_url": url,
                "amount": 12_000,
                "expires_at": expiry.isoformat(),
            },
        )

    async with mock_variza(container, monkeypatch, MockTransport(respond)):
        running = create_task(command.create(id, RETURN_URL))
        try:
            await wait_for(started.wait(), timeout=5)
            result = await command.create(id, RETURN_URL)
            assert result == LinkResult(failure=LinkFailure.UNKNOWN)
        finally:
            resume.set()
            link = await running
        assert link == LinkResult(link=Link(slug, url, expiry))
        assert await command.create(id, RETURN_URL) == link
    assert calls == 1
    async with container() as scope:
        payments = await scope.get(PaymentRepository)
        stored = await payments.get_by_id(id)
        assert stored is not None
        assert (
            stored.amount,
            stored.slug,
            stored.pay_url,
            stored.expires_at,
        ) == (
            120_000,
            slug,
            url,
            expiry,
        )


@pytest.mark.parametrize(
    ("status", "expected", "calls"),
    (
        (None, LinkFailure.UNKNOWN, 1),
        (201, LinkFailure.UNKNOWN, 1),
        (422, LinkFailure.REJECTED, 2),
        (429, LinkFailure.UNAVAILABLE, 2),
    ),
)
async def test_creation_outcome_controls_next_attempt(
    payment: tuple[AsyncContainer, int],
    monkeypatch: pytest.MonkeyPatch,
    status: int | None,
    expected: LinkFailure,
    calls: int,
) -> None:
    container, id = payment
    command = await container.get(ICreateLinkCommand)
    sent = 0

    def respond(request: Request) -> Response:
        nonlocal sent
        sent += 1
        if status is None:
            raise ReadTimeout("fixture timeout", request=request)
        return Response(status, json={"slug": "incomplete"})

    async with mock_variza(container, monkeypatch, MockTransport(respond)):
        assert await command.create(id, RETURN_URL) == LinkResult(
            failure=expected
        )
        assert await command.create(id, RETURN_URL) == LinkResult(
            failure=expected
        )
    assert sent == calls


async def test_invalid_amount_and_expired_link_skip_variza(
    payment: tuple[AsyncContainer, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    container, id = payment
    command = await container.get(ICreateLinkCommand)

    def respond(request: Request) -> Response:
        pytest.fail("Unexpected Variza request")

    async with mock_variza(container, monkeypatch, MockTransport(respond)):
        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            async with transaction():
                await payments.update_by_id(id, {"amount": 120_001})
        assert await command.create(id, RETURN_URL) == LinkResult(
            failure=LinkFailure.INVALID_AMOUNT
        )

        async with container() as scope:
            payments = await scope.get(PaymentRepository)
            record = await payments.get_by_id(id)
            assert record is not None and record.link_requested_at is None
            async with transaction():
                await payments.save_link(
                    id,
                    slug="expired-link",
                    pay_url="https://variza.ir/pay/expired-link",
                    expires_at=utc_now() - timedelta(seconds=1),
                )
        assert await command.create(id, RETURN_URL) == LinkResult(
            failure=LinkFailure.EXPIRED
        )
