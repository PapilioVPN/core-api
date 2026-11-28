"""Run real Panel HTTP streams, including client disconnects and keepalive."""

from asyncio import create_task, sleep, timeout
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from json import loads
from socket import socket

from fastapi import FastAPI
from httpx import AsyncClient, Response
from pydantic import JsonValue
from uvicorn import Config, Server


@asynccontextmanager
async def panel(app: FastAPI) -> AsyncIterator[AsyncClient]:
    with socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = Server(
            Config(
                app,
                lifespan="off",
                ws="none",
                log_config=None,
                access_log=False,
            )
        )
        task = create_task(server.serve(sockets=[listener]))
        try:
            async with timeout(5):
                while not server.started:
                    assert not task.done()
                    await sleep(0.01)
            async with AsyncClient(
                base_url=f"http://127.0.0.1:{port}", timeout=5
            ) as client:
                yield client
        finally:
            server.should_exit = True
            async with timeout(5):
                await task


async def events(
    reply: Response,
) -> AsyncIterator[tuple[str, dict[str, JsonValue]]]:
    event = ""
    data = None
    async for line in reply.aiter_lines():
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: "):
            data = loads(line[6:])
        elif not line and data is not None:
            yield event, data
            data = None
