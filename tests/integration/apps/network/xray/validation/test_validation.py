"""Validate proposed Xray configuration from the administrator API."""

import ssl
from hashlib import sha256
from pathlib import Path
from threading import get_ident
from typing import cast

import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.apps.network.xray.revisions.infra.crypto import digest
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration


async def test_validation_requires_configured_node(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    event_loop_thread = get_ident()

    def digest_in_worker(source: bytes) -> str:
        assert get_ident() != event_loop_thread
        return sha256(source).hexdigest()

    monkeypatch.setattr(digest, "digest_hex", digest_in_worker)
    headers = await admin_headers(
        app, client, mobile="09120000918", role_key="xray-unconfigured-test"
    )
    registered = await client.post(
        "/admin/nodes",
        headers=headers,
        json={
            "name": "Xray without access",
            "address": "xray-without-access.example.invalid",
            "port": 8081,
        },
    )
    assert registered.status_code == 201, registered.text
    node_id = registered.json()["data"]["id"]
    url = f"/admin/nodes/{node_id}/xray/instances/edge/config-validations"
    source = '{ "remarks": "برش Xray" }\n'
    response = await client.post(
        url, headers=headers, json={"config_json": source}
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"] == {
        "node_id": node_id,
        "instance_id": "edge",
        "config_sha256": sha256(source.encode()).hexdigest(),
        "status": "not_configured",
        "issue": None,
    }
    assert (
        await client.post(url, json={"config_json": source})
    ).status_code == 401
    assert (
        await client.post(
            url.replace("/edge/", "/Invalid/"),
            headers=headers,
            json={"config_json": source},
        )
    ).status_code == 422
    for body in ({}, {"config_json": "  \n"}, {"config_json": "آ" * 524_289}):
        invalid = await client.post(url, headers=headers, json=body)
        assert invalid.status_code == 422
        assert invalid.json()["errors"][0]["loc"] == ["config_json"]
        assert "آ" * 10 not in invalid.text


async def test_native_xray_validation_and_status(
    node_process: tuple[int, int, trustme.CA, Path],
    node_api_key: str,
    pg: CoreSettings,
    app: FastAPI,
    client: AsyncClient,
) -> None:
    grpc_port, http_port, ca, configured = node_process
    configured_bytes = configured.read_bytes()
    headers = await admin_headers(
        app, client, mobile="09120000919", role_key="xray-native-test"
    )
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        row = await nodes.create(
            NodeCreate(
                name="Isolated Xray validator",
                address="127.0.0.1",
                port=grpc_port,
            )
        )
    assert row.id is not None
    pg.node_host = NodeHostConfig.model_validate(
        {
            "targets": {
                row.id: {
                    "address": row.address,
                    "port": row.port,
                    "api_key": node_api_key,
                    "ca_pem": ca.cert_pem.bytes().decode(),
                }
            }
        }
    )
    url = f"/admin/nodes/{row.id}/xray/instances/edge/config-validations"
    panel_status = url.removesuffix("/config-validations")
    host_reply = await client.get(
        f"/admin/nodes/{row.id}/host-stats", headers=headers
    )
    assert host_reply.status_code == 200, host_reply.text
    assert host_reply.json()["data"]["status"] in {"available", "partial"}

    tls = ssl.create_default_context()
    ca.configure_trust(tls)
    async with AsyncClient(
        base_url=f"https://127.0.0.1:{http_port}",
        headers={"x-api-key": node_api_key},
        verify=tls,
    ) as node_http:
        status_url = "/v1/xray/instances/edge"
        before = await node_http.get(status_url)
        assert before.status_code == 200, before.text
        assert before.json()["state"] == "stopped"
        observed = await client.get(panel_status, headers=headers)
        assert observed.status_code == 200, observed.text
        data = observed.json()["data"]
        assert data["status"] == "observed"
        assert data["instance"]["state"] == "stopped"
        assert data["instance"]["applied_config_sha256"] is None
        missing = await client.get(
            panel_status.removesuffix("/edge") + "/missing", headers=headers
        )
        assert missing.json()["data"]["status"] == "instance_not_found"

        candidate = '{ "outbounds": [{"protocol":"freedom","tag":"new"}] }\n'
        reply = await client.post(
            url, headers=headers, json={"config_json": candidate}
        )
        assert reply.status_code == 200, reply.text
        assert reply.json()["data"] == {
            "node_id": row.id,
            "instance_id": "edge",
            "config_sha256": sha256(candidate.encode()).hexdigest(),
            "status": "valid",
            "issue": None,
        }

        stored = await client.post(
            "/admin/xray/revisions",
            headers=headers,
            json={"config_json": candidate},
        )
        assert stored.status_code == 201, stored.text
        revision = stored.json()["data"]
        revision_url = url.replace(
            "/config-validations",
            f"/config-revisions/{revision['id']}/validations",
        )
        saved_reply = await client.post(revision_url, headers=headers)
        assert saved_reply.status_code == 200, saved_reply.text
        assert saved_reply.json()["data"] == {
            "revision_id": revision["id"],
            "validation": reply.json()["data"],
        }

        for proposal, expected in (
            ('{ "outbounds": ', "config_decode_error"),
            (
                '{"outbounds":[{"protocol":"unknown-test-protocol"}]}',
                "config_rejected",
            ),
        ):
            reply = await client.post(
                url, headers=headers, json={"config_json": proposal}
            )
            assert reply.status_code == 200, reply.text
            assert reply.json()["data"]["status"] == "invalid"
            assert reply.json()["data"]["issue"]["code"] == expected
            assert (
                reply.json()["data"]["config_sha256"]
                == sha256(proposal.encode()).hexdigest()
            )
            assert proposal not in reply.text

        absent = await client.post(
            url.replace("/edge/", "/missing/"),
            headers=headers,
            json={"config_json": candidate},
        )
        assert absent.status_code == 200, absent.text
        assert absent.json()["data"]["status"] == "instance_not_found"
        after = await node_http.get(status_url)
        assert after.json() == before.json()
        assert configured.read_bytes() == configured_bytes

        # Change lifecycle only in the isolated test, not through Core.
        launched = await node_http.put(f"{status_url}/execution", timeout=10)
        assert launched.status_code == 200, launched.text
        observed = await client.get(panel_status, headers=headers)
        assert observed.status_code == 200, observed.text
        engine = observed.json()["data"]["instance"]
        assert engine["state"] == "ready"
        assert engine["xray_version"] and engine["node_version"]
        assert (
            engine["applied_config_sha256"]
            == sha256(configured_bytes).hexdigest()
        )
