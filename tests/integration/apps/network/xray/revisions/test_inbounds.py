"""Read the declared inbound choices from one saved Xray revision."""

from json import dumps
from threading import get_ident

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from papilio.infra.db.transaction import active_transaction
from sqlalchemy import event
from sqlalchemy.engine import Engine

from src.apps.network.xray.revisions.app.queries import (
    inbounds as query_module,
)
from src.apps.network.xray.revisions.domain.enums.inbounds import (
    XrayRevisionInboundFailure,
)
from src.apps.network.xray.revisions.domain.results.inbounds import (
    XrayRevisionInbound,
)

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_REVISIONS = "/admin/xray/revisions"


async def test_revision_inbounds_return_only_safe_declared_fields(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await admin_headers(
        app, client, mobile="09120000689", role_key="xray-revision-inbounds"
    )

    async def save(document: dict[str, object]) -> str:
        response = await client.post(
            _REVISIONS,
            headers=headers,
            json={"config_json": dumps(document)},
        )
        assert response.status_code == 201, response.text
        id = response.json()["data"]["id"]
        return f"{_REVISIONS}/{id}/inbounds"

    tag = "edge-transport"
    key = "isolated-inbound-secret-marker"
    path = await save(
        {
            "inbounds": [
                {
                    "tag": tag,
                    "protocol": "vless",
                    "streamSettings": {
                        "network": "ws",
                        "security": "tls",
                        "tlsSettings": {"privateKey": key},
                    },
                    "settings": {"clients": [{"id": key}]},
                },
                {"protocol": "dokodemo-door"},
                {"tag": "aux", "protocol": "socks"},
            ]
        }
    )
    assert (await client.get(path)).status_code == 401
    loop_thread = get_ident()
    project = query_module.project_inbounds

    def project_in_worker(
        source: bytes,
    ) -> tuple[XrayRevisionInbound, ...] | XrayRevisionInboundFailure:
        assert get_ident() != loop_thread
        assert active_transaction() is None
        return project(source)

    monkeypatch.setattr(query_module, "project_inbounds", project_in_worker)
    statements: list[str] = []

    def capture_sql(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        sql = statement.strip().lower()
        if "tbl_xray_revisions" in sql:
            statements.append(sql.split(None, 1)[0])

    event.listen(Engine, "before_cursor_execute", capture_sql)
    try:
        response = await client.get(path, headers=headers)
    finally:
        event.remove(Engine, "before_cursor_execute", capture_sql)
    assert statements == ["select"]
    assert response.status_code == 200, response.text
    assert key not in response.text
    assert response.json()["data"] == [
        {"tag": tag, "protocol": "vless", "network": "ws", "security": "tls"},
        {"tag": "aux", "protocol": "socks", "network": None, "security": None},
    ]
    assert "no-store" in response.headers["Cache-Control"]

    empty_documents: tuple[dict[str, object], ...] = (
        {"remarks": "empty inbound selection"},
        {"inbounds": None},
    )
    for document in empty_documents:
        empty = await save(document)
        response = await client.get(empty, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["data"] == []

    for inbounds in (
        {"private": key},
        [
            {"tag": "duplicate", "protocol": "vless"},
            {"tag": "duplicate", "protocol": "socks"},
        ],
        [{"tag": tag, "protocol": "vless", "streamSettings": key}],
    ):
        invalid = await save({"inbounds": inbounds})
        response = await client.get(invalid, headers=headers)
        assert response.status_code == 422, response.text
        assert response.json()["error"]["message_code"] == (
            "xray_revision_inbounds_invalid"
        )
        assert key not in response.text
    missing = await client.get(
        f"{_REVISIONS}/9999999/inbounds", headers=headers
    )
    assert missing.status_code == 404, missing.text
