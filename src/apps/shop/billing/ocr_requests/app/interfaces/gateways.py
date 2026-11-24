"""Recognize text from a bounded image sent to the configured engine."""

from typing import Protocol

from ...domain.results.records import OCRFailure


class IOCRGateway(Protocol):
    async def read(self, image: bytes) -> tuple[str, ...] | OCRFailure: ...
