"""Native Xray process fixtures shared by Network capabilities."""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ
from pathlib import Path

import pytest
import trustme
import yaml

type RunningXrayNode = tuple[int, int, trustme.CA, Path]


@pytest.fixture
def node_api_key() -> str:
    return "isolated-xray-native-validation-key"


@pytest.fixture
def node_xray_overrides() -> dict[str, bool]:
    return {}


@pytest.fixture
async def node_process(
    tmp_path: Path,
    node_api_key: str,
    node_xray_overrides: dict[str, bool],
) -> AsyncIterator[RunningXrayNode]:
    async with _run_node(tmp_path, node_api_key, node_xray_overrides) as node:
        yield node


@pytest.fixture
async def node_pair(
    tmp_path: Path,
    node_api_key: str,
    node_xray_overrides: dict[str, bool],
) -> AsyncIterator[tuple[RunningXrayNode, RunningXrayNode]]:
    async with (
        _run_node(tmp_path / "node-a", node_api_key, node_xray_overrides) as a,
        _run_node(tmp_path / "node-b", node_api_key, node_xray_overrides) as b,
    ):
        yield a, b


@asynccontextmanager
async def _run_node(
    directory: Path,
    node_api_key: str,
    node_xray_overrides: dict[str, bool],
) -> AsyncIterator[RunningXrayNode]:
    node = environ.get("PAPILIOVPN_TEST_NODE_BIN")
    xray = environ.get("PAPILIOVPN_TEST_XRAY_BIN")
    if not node or not xray:
        pytest.skip("Set isolated Node and Xray executable paths")
    directory.mkdir(exist_ok=True)
    ca = trustme.CA()
    certificate = ca.issue_cert("127.0.0.1")
    certificate.private_key_pem.write_to_path(directory / "tls.key")
    certificate.cert_chain_pems[0].write_to_path(directory / "tls.crt")
    configured = directory / "configured.json"
    configured.write_text(
        '{"outbounds":[{"protocol":"freedom"}],"observatory":{}}'
    )
    config = directory / "node.yml"
    config.write_text(
        yaml.safe_dump(
            {
                "management": {
                    "http_address": "127.0.0.1:0",
                    "grpc_address": "127.0.0.1:0",
                    "api_key": node_api_key,
                    "tls": {"cert_file": "tls.crt", "key_file": "tls.key"},
                },
                "xray": {
                    "id": "edge",
                    "executable": str(Path(xray).resolve()),
                    "config_file": str(configured),
                    "runtime_directory": str(directory),
                    **node_xray_overrides,
                },
            }
        )
    )
    process = await asyncio.create_subprocess_exec(
        str(Path(node).resolve()),
        "-config",
        str(config),
        cwd=directory,
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
