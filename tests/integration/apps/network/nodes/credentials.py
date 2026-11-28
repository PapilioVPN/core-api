from typing import cast

from dishka import AsyncContainer
from fastapi import FastAPI
from pydantic import SecretStr

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)
from src.apps.network.nodes.registry.domain.dtos.records import NodeUpdate


async def enroll_nodes(
    app: FastAPI, credentials: dict[int, tuple[str, str | None]]
) -> None:
    container = cast(AsyncContainer, app.state.dishka_container)
    async with container() as scope:
        nodes = await scope.get(INodeService)
        for node_id, (api_key, ca_pem) in credentials.items():
            await nodes.update(
                node_id, NodeUpdate(api_key=SecretStr(api_key), ca_pem=ca_pem)
            )
