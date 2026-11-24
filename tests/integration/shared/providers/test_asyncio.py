"""Native DI scope and worker execution for shared asyncio adapters."""

import os
import threading

import pytest
from dishka import make_async_container

from src.shared.providers.asyncio import AsyncioProvider
from src.shared.utils.asyncio.processes import ProcessRunner
from src.shared.utils.asyncio.threads import ThreadRunner

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_app_runners_are_shared_across_requests_and_execute() -> None:
    container = make_async_container(AsyncioProvider())
    try:
        async with container() as first:
            threads = await first.get(ThreadRunner)
            processes = await first.get(ProcessRunner)
            worker_thread = await threads.run(threading.get_ident)
            worker_process = await processes.run(os.getpid)
            assert worker_thread != threading.get_ident()
            assert worker_process != os.getpid()
        async with container() as second:
            assert await second.get(ThreadRunner) is threads
            assert await second.get(ProcessRunner) is processes
            assert await threads.run(os.getpid) == os.getpid()
    finally:
        await container.close()
