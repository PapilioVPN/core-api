"""Verify WireGuard membership is read through the authorized Panel API."""

from base64 import b64encode
from typing import cast

import grpc
import pytest
import trustme
from dishka import AsyncContainer
from fastapi import FastAPI
from grpc import aio
from httpx import AsyncClient

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.dtos.records import NodeCreate
from src.apps.network.wireguard.interfaces.infra.grpc.v1 import (
    interfaces_pb2 as wire,
)
from src.apps.network.wireguard.interfaces.infra.grpc.v1 import (
    interfaces_pb2_grpc as rpc,
)
from src.settings.config import CoreSettings
from tests.integration.apps.network.nodes.credentials import enroll_nodes

from ...nodes.auth import admin_headers

pytestmark = pytest.mark.integration
_NODE_KEY = "isolated-wireguard-membership-test"


async def test_membership_identifies_absent_registry_target(
    app: FastAPI, client: AsyncClient
) -> None:
    path = "/admin/nodes/9999999/wireguard/interfaces/wg-test/peers"
    headers = await admin_headers(
        app, client, mobile="09120000691", role_key="wireguard-peer-read"
    )
    denied = await client.get(path)
    assert denied.status_code == 401, denied.text
    absent = await client.get(path, headers=headers)
    assert absent.status_code == 404, absent.text
    assert absent.json()["error"]["entity"] == "Node"


class MembershipPeer(rpc.WireGuardInterfacesServiceServicer):
    members = [
        wire.WireGuardPeerMember(
            public_key=bytes(range(32)),
            allowed_ips=["192.0.2.2/32", "2001:db8::/64"],
        )
    ]

    async def ListPeers(
        self,
        request: wire.WireGuardInterfaceRequest,
        context: aio.ServicerContext[
            wire.WireGuardInterfaceRequest, wire.WireGuardPeerMembership
        ],
    ) -> wire.WireGuardPeerMembership:
        metadata = tuple(context.invocation_metadata() or ())
        assert ("x-api-key", _NODE_KEY) in metadata
        assert request.name == "wg-test"
        return wire.WireGuardPeerMembership(peers=self.members)


async def test_membership_preserves_public_fields_and_empty_snapshot(
    app: FastAPI, client: AsyncClient, pg: CoreSettings
) -> None:
    ca = trustme.CA()
    cert = ca.issue_cert("127.0.0.1")
    server = aio.server()
    peer = MembershipPeer()
    rpc.add_WireGuardInterfacesServiceServicer_to_server(peer, server)
    port = server.add_secure_port(
        "127.0.0.1:0",
        grpc.ssl_server_credentials(
            [(cert.private_key_pem.bytes(), cert.cert_chain_pems[0].bytes())],
        ),
    )
    await server.start()
    try:
        headers = await admin_headers(
            app, client, mobile="09120000692", role_key="wireguard-peer-native"
        )
        container = cast(AsyncContainer, app.state.dishka_container)
        async with container() as scope:
            nodes = await scope.get(INodeService)
            node = await nodes.create(
                NodeCreate(
                    name="WireGuard peer", address="127.0.0.1", port=port
                )
            )
        await enroll_nodes(
            app,
            {
                node.id: (_NODE_KEY, ca.cert_pem.bytes().decode()),
            },
        )
        path = f"/admin/nodes/{node.id}/wireguard/interfaces/wg-test/peers"
        response = await client.get(path, headers=headers)
        assert response.status_code == 200, response.text
        row = response.json()["data"]
        assert row["status"] == "observed"
        assert row["received_at"] is not None
        assert row["peers"] == [
            {
                "public_key": b64encode(bytes(range(32))).decode(),
                "allowed_ips": ["192.0.2.2/32", "2001:db8::/64"],
            }
        ]
        peer.members = []
        empty = await client.get(path, headers=headers)
        assert empty.json()["data"]["status"] == "observed"
        assert empty.json()["data"]["peers"] == []
        peer.members = [wire.WireGuardPeerMember(public_key=b"invalid")]
        invalid = await client.get(path, headers=headers)
        assert invalid.json()["data"]["status"] == "failed"
        assert invalid.json()["data"]["peers"] is None
    finally:
        await server.stop(None)
