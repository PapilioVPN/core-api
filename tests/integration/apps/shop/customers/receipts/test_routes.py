"""Register customer receipts and read their protected images."""

from base64 import b64decode
from pathlib import Path

import pytest
from httpx import AsyncClient

from src.settings.config import CoreSettings

pytestmark = pytest.mark.integration
PNG = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lE"
    "QVR42mP8/x8AAwMCAO+aJ1sAAAAASUVORK5CYII="
)


@pytest.fixture
def pg(pg: CoreSettings, tmp_path: Path) -> CoreSettings:
    pg.storage.path = str(tmp_path / "media")
    pg.storage.temp_dir = str(tmp_path / "staging")
    pg.storage.max_file_size = 1024
    return pg


@pytest.mark.parametrize("admin", [("074", True)], indirect=True)
async def test_receipt_upload(
    client: AsyncClient, admin: dict[str, str], tmp_path: Path
) -> None:
    customer = await client.post(
        "/admin/customers", headers=admin, json={"name": "Receipt Customer"}
    )
    assert customer.status_code == 201
    customer_id = customer.json()["data"]["id"]
    path = f"/admin/customers/{customer_id}/receipts"
    headers = admin | {"Content-Type": "image/png"}
    amount = {"amount": 4_000_000_005}
    assert (
        await client.post(path, params=amount, content=PNG)
    ).status_code == 401

    for content, code in ((b"not an image", 400), (PNG * 1024, 413)):
        invalid = await client.post(
            path, params=amount, headers=headers, content=content
        )
        assert invalid.status_code == code, invalid.text
    invalid = await client.post(
        path, params={"amount": 0}, headers=headers, content=PNG
    )
    assert invalid.status_code == 422
    invalid = await client.post(
        path,
        params=amount,
        headers=admin | {"Content-Type": "image/jpeg"},
        content=PNG,
    )
    assert invalid.status_code == 400
    missing = await client.post(
        "/admin/customers/99999/receipts",
        params=amount,
        headers=headers,
        content=PNG,
    )
    assert missing.status_code == 404
    assert not list((tmp_path / "media").glob("*/*"))

    response = await client.post(
        path, params=amount, headers=headers, content=PNG
    )
    assert response.status_code == 201, response.text
    receipt = response.json()["data"]
    assert receipt["amount"] == amount["amount"]
    assert receipt["customer_id"] == customer_id
    assert receipt["status"] == "pending"
    address = receipt["image_url"]
    assert "file_id" not in receipt
    detail = await client.get(
        f"/admin/receipts/{receipt['id']}", headers=admin
    )
    assert detail.json()["data"] == receipt
    assert (await client.get(address)).status_code == 401
    image = await client.get(address, headers=admin)
    assert image.status_code == 200
    assert image.content == PNG
    assert image.headers["content-type"] == "image/png"

    key = f"{'a' * 64}.png"
    orphan = tmp_path / "media" / key[:2] / key
    orphan.parent.mkdir(exist_ok=True)
    orphan.write_bytes(PNG)
    missing = await client.get(f"/admin/receipts/images/{key}", headers=admin)
    assert missing.status_code == 404
    orphan.unlink()

    again = await client.post(
        path, params=amount, headers=headers, content=PNG
    )
    assert again.status_code == 201
    assert again.json()["data"]["image_url"] == address
    assert len(list((tmp_path / "media").glob("*/*"))) == 1
    assert not list((tmp_path / "staging").iterdir())


@pytest.mark.parametrize("admin", [("075", False)], indirect=True)
async def test_receipts_require_customer_scope(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    response = await client.post(
        "/admin/customers/1/receipts",
        params={"amount": 10000},
        headers=admin | {"Content-Type": "image/png"},
        content=PNG,
    )
    assert response.status_code == 403
    image = await client.get(
        f"/admin/receipts/images/{'a' * 64}.png", headers=admin
    )
    assert image.status_code == 403
