"""Observe live aggregate VLESS membership without exposing account data."""

import ssl
from json import dumps
from pathlib import Path
from socket import socket
from typing import cast
from uuid import uuid4

import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import AsyncClient

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.config import NodeHostConfig
from src.apps.network.nodes.domain.dtos.records import NodeCreate
from src.settings.config import CoreSettings

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_BASE = "/admin/nodes/{id}/xray/instances/edge/accounts/vless/count"


async def test_vless_count_requires_network_authentication(
    client: AsyncClient,
) -> None:
    response = await client.get(
        _BASE.format(id=1), params={"inbound_tag": "real"}
    )
    assert response.status_code == 401, response.text


async def test_vless_count_reads_true_membership(
    app: FastAPI,
    client: AsyncClient,
    pg: CoreSettings,
    node_process: tuple[int, int, trustme.CA, Path],
    node_api_key: str,
) -> None:
    grpc_port, http_port, ca, config = node_process
    with socket() as first, socket() as second:
        first.bind(("127.0.0.1", 0))
        second.bind(("127.0.0.1", 0))
        ports = [first.getsockname()[1], second.getsockname()[1]]
    config.write_text(
        dumps(
            {
                "inbounds": [
                    {
                        "tag": tag,
                        "listen": "127.0.0.1",
                        "port": port,
                        "protocol": "vless",
                        "settings": {"decryption": "none", "clients": members},
                    }
                    for port, tag, members in zip(
                        ports,
                        ("real", "empty"),
                        (
                            [
                                {
                                    "id": str(uuid4()),
                                    "email": "fixture@example.invalid",
                                }
                            ],
                            [],
                        ),
                        strict=True,
                    )
                ],
                "outbounds": [{"protocol": "freedom"}],
            }
        )
    )
    tls = ssl.create_default_context()
    ca.configure_trust(tls)
    async with AsyncClient(
        verify=tls, headers={"X-API-Key": node_api_key}
    ) as native:
        started = await native.put(
            f"https://127.0.0.1:{http_port}/v1/xray/instances/edge/execution",
            timeout=10,
        )
        assert started.is_success, started.text
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        node = await nodes.create(
            NodeCreate(
                name="Isolated VLESS membership",
                address="127.0.0.1",
                port=grpc_port,
            )
        )
    pg.node_host = NodeHostConfig.model_validate(
        {
            "targets": {
                node.id: {
                    "address": node.address,
                    "port": grpc_port,
                    "api_key": node_api_key,
                    "ca_pem": ca.cert_pem.bytes().decode(),
                }
            }
        }
    )
    headers = await admin_headers(
        app, client, mobile="09120000773", role_key="native-vless-count"
    )
    for tag, count, status in [
        ("real", 1, "observed"),
        ("empty", 0, "observed"),
        ("missing", None, "target_not_found"),
    ]:
        reply = await client.get(
            _BASE.format(id=node.id),
            headers=headers,
            params={"inbound_tag": tag},
        )
        assert reply.status_code == 200, reply.text
        assert "fixture@example.invalid" not in reply.text
        result = reply.json()["data"]
        assert (result["inbound_tag"], result["count"], result["status"]) == (
            tag,
            count,
            status,
        )
