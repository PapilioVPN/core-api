"""Receipt extraction used by the Events worker."""

from typing import Protocol


class IOCRPipeline(Protocol):
    async def process(self, receipt_id: int, *, event_id: str) -> None: ...
