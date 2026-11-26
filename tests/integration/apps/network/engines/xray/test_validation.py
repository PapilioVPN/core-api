"""Validate proposed Xray configuration from the administrator API."""

import asyncio
import json
import ssl
from collections.abc import AsyncIterator
from hashlib import sha256
from os import environ
from pathlib import Path
from typing import cast

import pytest
import trustme
import yaml
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_KEY = "isolated-xray-native-validation-key"


async def test_validation_requires_configured_node(
    app: FastAPI, client: AsyncClient
) -> None:
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


@pytest.fixture
async def node_process(
    tmp_path: Path,
) -> AsyncIterator[tuple[int, int, trustme.CA, Path]]:
    node = environ.get("PAPILIOVPN_TEST_NODE_BIN")
    xray = environ.get("PAPILIOVPN_TEST_XRAY_BIN")
    if not node or not xray:
        pytest.skip("Set isolated Node and Xray executable paths")
    ca = trustme.CA()
    certificate = ca.issue_cert("127.0.0.1")
    certificate.private_key_pem.write_to_path(tmp_path / "tls.key")
    certificate.cert_chain_pems[0].write_to_path(tmp_path / "tls.crt")
    configured = tmp_path / "configured.json"
    configured.write_text('{"outbounds":[{"protocol":"freedom"}]}')
    config = tmp_path / "node.yml"
    config.write_text(
        yaml.safe_dump(
            {
                "management": {
                    "http_address": "127.0.0.1:0",
                    "grpc_address": "127.0.0.1:0",
                    "api_key": _KEY,
                    "tls": {"cert_file": "tls.crt", "key_file": "tls.key"},
                },
                "xray": {
                    "id": "edge",
                    "executable": str(Path(xray).resolve()),
                    "config_file": str(configured),
                    "runtime_directory": str(tmp_path),
                },
            }
        )
    )
    process = await asyncio.create_subprocess_exec(
        str(Path(node).resolve()),
        "-config",
        str(config),
        cwd=tmp_path,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        assert process.stderr is not None
        async with asyncio.timeout(10):
            while line := await process.stderr.readline():
                event = json.loads(line)
                if event.get("msg") == "management listeners ready":
                    break
            else:
                pytest.fail(
                    "Node exited before its management listeners bound"
                )
        yield event["grpc"]["Port"], event["http"]["Port"], ca, configured
    finally:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.communicate(), timeout=5)
            except TimeoutError:
                process.kill()
                await process.communicate()


async def test_xray_validates_candidate_without_applying_it(
    node_process: tuple[int, int, trustme.CA, Path],
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
                    "api_key": _KEY,
                    "ca_pem": ca.cert_pem.bytes().decode(),
                }
            }
        }
    )
    url = f"/admin/nodes/{row.id}/xray/instances/edge/config-validations"
    host_reply = await client.get(
        f"/admin/nodes/{row.id}/host-stats", headers=headers
    )
    assert host_reply.status_code == 200, host_reply.text
    assert host_reply.json()["data"]["status"] in {"available", "partial"}

    tls = ssl.create_default_context()
    ca.configure_trust(tls)
    async with AsyncClient(
        base_url=f"https://127.0.0.1:{http_port}",
        headers={"x-api-key": _KEY},
        verify=tls,
    ) as node_http:
        status_url = "/v1/xray/instances/edge"
        before = await node_http.get(status_url)
        assert before.status_code == 200, before.text
        assert before.json()["state"] == "stopped"

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
