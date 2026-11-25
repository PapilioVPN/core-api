"""Native application checks against an invocation-owned database."""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.bootstrap.api import create_api
from src.settings.config import CoreSettings


@pytest.fixture
def settings(pytestconfig: pytest.Config) -> CoreSettings:
    sample: Path = pytestconfig.rootpath / "config.yml.sample"
    data = yaml.safe_load(sample.read_text(encoding="utf-8"))
    data["crypto"]["password_salt"] = "test-only-password-pepper-not-for-use"
    data["crypto"]["encryption_key"] = "test-only-gateway-encryption-key"
    data["jwt"]["secret_key"] = "test-only-token-signing-key-not-for-use"
    return CoreSettings.model_validate(data)


@pytest.fixture
def pg(settings: CoreSettings) -> CoreSettings:
    dsn = os.environ.get("PAPILIOVPN_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set PAPILIOVPN_TEST_POSTGRES_DSN to the isolated test DB")
    assert settings.db is not None
    settings.db.dsn = dsn
    return settings


@pytest.fixture
def app(pg: CoreSettings) -> FastAPI:
    return create_api(pg)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with (
        app.router.lifespan_context(app),
        AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client,
    ):
        yield client
