"""Exercise Billing previews against native PostgreSQL and Redis."""

from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.errors.exceptions import ForbiddenException, NotFoundException
from papilio.infra.redis.client import RedisClient, resolve

from src.apps.shop.billing.invoices.app.interfaces.commands import (
    IInvoiceCommand,
)
from src.apps.shop.billing.invoices.app.interfaces.services import (
    IInvoiceService,
)
from src.apps.shop.billing.invoices.domain.dtos.records import TopupInput
from src.apps.shop.customers.profiles.app.interfaces.services import (
    ICustomerService,
)
from src.apps.shop.customers.profiles.domain.dtos.records import ProfileCreate
from src.apps.shop.products.catalogs.app.interfaces.commands import (
    ICatalogCommand,
)
from src.apps.shop.products.catalogs.domain.dtos.records import (
    CatalogCreate,
    CatalogUpdate,
)
from src.apps.shop.products.catalogs.domain.enums.records import CatalogStatus
from src.apps.shop.products.services.app.interfaces.services import (
    IShopService,
)
from src.apps.shop.products.services.domain.dtos.records import ServiceCreate
from src.apps.shop.products.volume_ranges.app.interfaces.commands import (
    IRangeCommand,
)
from src.apps.shop.products.volume_ranges.domain.dtos.quote import QuoteInput
from src.apps.shop.products.volume_ranges.domain.dtos.records import RangeWrite

pytestmark = pytest.mark.integration


async def test_billing_previews(app: FastAPI, client: AsyncClient) -> None:
    store = cast(AsyncContainer, app.state.dishka_container)
    redis = await store.get(RedisClient | None)
    if redis is None:
        pytest.skip("Set PAPILIOVPN_TEST_REDIS_URL to isolated Redis")

    gib = 1024**3
    async with store() as scope:
        customers = await scope.get(ICustomerService)
        services = await scope.get(IShopService)
        catalogs = await scope.get(ICatalogCommand)
        ranges = await scope.get(IRangeCommand)
        customer = await customers.create(
            ProfileCreate(name="Invoice Customer")
        )
        other = await customers.create(ProfileCreate(name="Another Customer"))
        blocked = await customers.create(
            ProfileCreate(name="Blocked Customer", is_blocked=True)
        )
        service = await services.create(ServiceCreate(title="Preview Service"))
        catalog = await catalogs.create(
            CatalogCreate(
                service_id=service.id,
                title="Published Catalog",
                price=120_000,
                status=CatalogStatus.PUBLISHED,
            )
        )
        draft = await catalogs.create(
            CatalogCreate(
                service_id=service.id, title="Draft Catalog", price=20_000
            )
        )
        rule = await ranges.create(
            service.id,
            RangeWrite(
                min_bytes=gib,
                max_bytes=3 * gib,
                step_bytes=gib,
                price_per_gib=50_000,
            ),
        )

    async with store() as scope:
        create = await scope.get(IInvoiceCommand)
        before = datetime.now(UTC)
        topup = await create.topup(customer.id, TopupInput(amount=210_000))
        fixed = await create.catalog(customer.id, catalog.id)
        custom = await create.range(
            customer.id, service.id, QuoteInput(volume_bytes=2 * gib)
        )
        assert before + timedelta(hours=1) <= topup.expires_at
        assert topup.expires_at <= datetime.now(UTC) + timedelta(hours=1)
        assert topup.details.kind == "topup" and topup.amount == 210_000
        assert fixed.details.kind == "catalog"
        assert (
            fixed.details.catalog_id == catalog.id and fixed.amount == 120_000
        )
        assert custom.details.kind == "range"
        assert custom.details.range_id == rule.id and custom.amount == 100_000
        assert (
            custom.details.volume_bytes == 2 * gib
            and custom.details.days is None
        )
        with pytest.raises(ForbiddenException):
            await create.topup(blocked.id, TopupInput(amount=210_000))
        with pytest.raises(NotFoundException):
            await create.catalog(customer.id, draft.id)
        catalogs = await scope.get(ICatalogCommand)
        await catalogs.update(catalog.id, CatalogUpdate(price=150_000))

    invoices = await store.get(IInvoiceService)
    assert await invoices.get(customer.id, fixed.id) == fixed
    assert (await invoices.get(customer.id, fixed.id)).amount == 120_000
    with pytest.raises(NotFoundException):
        await invoices.get(other.id, fixed.id)

    key = f"shop:billing:invoices:{customer.id}:{topup.id}"
    assert await resolve(redis.client.type(key)) == "hash"
    ttl = await resolve(redis.client.ttl(key))
    assert 3500 < ttl <= 3600
    await resolve(redis.client.pexpireat(key, 0))
    with pytest.raises(NotFoundException):
        await invoices.get(customer.id, topup.id)
