"""Native SDK integration against a bounded, controlled loopback S3 peer."""

import hashlib
import shutil
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from pydantic import HttpUrl

from src.apps.core.storage.providers.domain.dtos.configs import S3Config


@dataclass
class S3Peer:
    root: Path
    config: S3Config | None = None
    error: tuple[int, str] | None = None
    delay: float = 0
    body_delay: float = 0
    started: threading.Event = field(default_factory=threading.Event)
    content_types: dict[str, str] = field(default_factory=dict)
    requested_keys: list[str] = field(default_factory=list)
    access_keys: list[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def path(self, key: str) -> Path:
        return self.root / hashlib.sha256(key.encode()).hexdigest()


@pytest.fixture
def s3_peer(tmp_path: Path) -> Iterator[S3Peer]:
    peer = S3Peer(tmp_path / "objects")
    peer.root.mkdir()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

        def error(self, status: int, code: str) -> None:
            body = f"<Error><Code>{code}</Code></Error>".encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_PUT(self) -> None:
            assert self.headers["If-None-Match"] == "*"
            assert self.headers["Authorization"].startswith("AWS4-HMAC-SHA256")
            remaining = int(self.headers["Content-Length"])
            path = peer.path(self.path)
            # A lock belongs to this controlled peer, not application storage.
            with peer.lock:
                with path.with_suffix(".partial").open("wb") as output:
                    while remaining:
                        block = self.rfile.read(min(65536, remaining))
                        assert block
                        output.write(block)
                        remaining -= len(block)
                peer.started.set()
                time.sleep(peer.delay)
                if peer.error:
                    path.with_suffix(".partial").unlink()
                    self.error(*peer.error)
                elif path.exists():
                    path.with_suffix(".partial").unlink()
                    self.error(412, "PreconditionFailed")
                else:
                    path.with_suffix(".partial").rename(path)
                    peer.content_types[self.path] = self.headers[
                        "Content-Type"
                    ]
                    self.send_response(200)
                    self.send_header("Content-Length", "0")
                    self.end_headers()

        def do_GET(self) -> None:
            peer.requested_keys.append(self.path)
            authorization = self.headers["Authorization"]
            peer.access_keys.append(
                authorization.partition("Credential=")[2].partition("/")[0]
            )
            peer.started.set()
            time.sleep(peer.delay)
            if peer.error:
                self.error(*peer.error)
                return
            path = peer.path(self.path)
            if not path.exists():
                self.error(404, "NoSuchKey")
                return
            self.send_response(200)
            self.send_header("Content-Length", str(path.stat().st_size))
            self.end_headers()
            time.sleep(peer.body_delay)
            try:
                with path.open("rb") as source:
                    shutil.copyfileobj(source, self.wfile, 65536)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    host, port = server.server_address[:2]
    peer.config = S3Config(
        bucket="test-bucket",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        endpoint_url=HttpUrl(f"http://{host}:{port}"),
        public_base_url=HttpUrl(f"http://{host}:{port}/test-bucket/"),
        region_name="us-east-1",
        addressing_style="path",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield peer
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def s3_config(s3_peer: S3Peer) -> S3Config:
    assert s3_peer.config is not None
    return s3_peer.config
