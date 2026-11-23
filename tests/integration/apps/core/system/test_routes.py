"""Verify the public System contract through Papilio's discovered router."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import URL

from src.bootstrap.api import create_api
from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration


async def test_missing_database(
    settings: CoreSettings, tmp_path: Path
) -> None:
    assert settings.db is not None
    settings.db.dsn = URL.create(
        "postgresql+asyncpg",
        username="test",
        database="test",
        query={"host": str(tmp_path / "missing-socket")},
    ).render_as_string()
    app = create_api(settings)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client,
    ):
        response = await client.get("/health")
        schema = await client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "nok"
    assert data["server_time"] is None
    assert data["duration_ms"] >= 0
    assert schema.status_code == 404


async def test_database_clock(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ok"
    assert data["server_time"]["datetime"]
    assert data["server_time"]["timezone"]
    assert data["duration_ms"] >= 0
