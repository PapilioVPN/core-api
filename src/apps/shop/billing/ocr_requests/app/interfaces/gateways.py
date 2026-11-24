"""Recognize text from a bounded image sent to the configured engine."""

from typing import Protocol


class IOCRGateway(Protocol):
    async def read(self, image: bytes) -> tuple[str, ...]: ...
